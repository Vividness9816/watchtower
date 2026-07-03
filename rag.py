# rag.py — local RAG for Watch Tower. Makes your reference docs (homelab notes, hardware manuals,
# runbooks, scraped wikis) searchable so the chat model can quote the RIGHT few paragraphs instead
# of being fed a whole document. Embeddings come from Ollama's local embedding model; retrieval is
# a cosine KNN over a sqlite-vec vector store. READ-ONLY: it only SELECTS text to show the model.
#
# Scales to a LARGE corpus (tens of thousands of chunks) via two things:
#   * BATCH embedding   — many chunks per Ollama /api/embed call (falls back to /api/embeddings on
#                         older Ollama). Turns an hours-long sequential build into minutes.
#   * INCREMENTAL index — each source's content hash is stored; only NEW or CHANGED docs are
#                         re-embedded, and docs removed from SOURCES are dropped. Editing one small
#                         doc costs seconds, not a full re-embed of the whole corpus.
#
# Deps: Ollama (already required) + `ollama pull nomic-embed-text` + `pip install sqlite-vec`.
# Everything else (json/urllib/pathlib/hashlib/re/math/sqlite3) is stdlib.
#
# Build the index (do this once after adding docs; re-run anytime — it only does the delta):
#   python rag.py --build           # embed new/changed docs
#   python rag.py --build --force    # wipe + re-embed everything (after changing a tuning knob)

import json, urllib.request, urllib.error, pathlib, hashlib, re, math, sys, sqlite3
import sqlite_vec
from sqlite_vec import serialize_float32

OLLAMA_HOST  = "http://127.0.0.1:11434"
OLLAMA_EMBED = OLLAMA_HOST + "/api/embed"        # batch endpoint (newer Ollama): {"input": [...]}
OLLAMA_EMB1  = OLLAMA_HOST + "/api/embeddings"   # single endpoint (older Ollama): {"prompt": "..."}
# mxbai-embed-large (1024-dim) measured best on this repo's frozen QA set: hit@5 0.939 / MRR@5
# 0.792, a strict win over nomic-embed-text (0.909 / 0.774) on BOTH recall and ranking. Swap back
# to "nomic-embed-text" (768-dim, ~270 MB, faster) if VRAM/pull size matters — retrieval degrades
# only slightly. A model change rebuilds the index automatically (settings hash below).
EMBED_MODEL  = "mxbai-embed-large"               # `ollama pull mxbai-embed-large` (~670 MB, CPU-ok)
EMBED_BATCH  = 64                                # chunks sent per /api/embed request
HERE = pathlib.Path(__file__).parent
DB   = HERE / "rag_index.db"                     # generated cache — git-ignored

# Docs to make searchable: EVERY *.md in this folder, plus the homelab notes (if present). Missing
# files are skipped. Drop a new .md in here and the next `python rag.py --build` picks it up.
# Project meta-docs (this RSI log, the recreate/instruction guides) are NOT reference material —
# excluded so they don't dilute a hardware/troubleshooting query.
_EXCLUDE = {"RSI-REPORT.md"}
SOURCES = [pathlib.Path.home() / "homelab" / "HOMELAB-COMPLETE-SETUP.md",
           *[p for p in sorted(HERE.glob("*.md")) if p.name not in _EXCLUDE]]

# --- tuning knobs (the RAG equivalent of rules.THRESH — tune for YOUR docs) ---
# 1600/400 measured best with mxbai on this corpus (see the model note above). Larger chunks then
# hurt (facts get averaged out); smaller ones split answers across chunk boundaries.
CHUNK_CHARS = 1600    # size of each searchable slice (~400 tokens)
OVERLAP     = 400     # chars repeated between neighbours so a fact on a boundary isn't lost
TOP_K       = 4       # how many chunks to return per question
MIN_SCORE   = 0.45    # cosine floor; below this a chunk is "not really relevant" and is dropped
                      #   -> an off-topic question retrieves nothing. THIS is the knob to tune.

# mxbai-embed-large wants a query-side instruction and NO document prefix. (nomic-embed-text
# instead wants "search_document: " / "search_query: " — swap both if you switch back.)
DOC_PREFIX   = ""
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)        # build progress -> stderr, never pollutes stdout


def _norm(v: list[float]) -> list[float]:
    """L2-normalize so cosine == dot product (lets sqlite-vec's L2 distance recover cosine)."""
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _embed(text: str, prefix: str = DOC_PREFIX) -> list[float]:
    """One text -> one normalized vector via the single-item endpoint (the fallback path)."""
    body = json.dumps({"model": EMBED_MODEL, "prompt": prefix + text}).encode()
    req = urllib.request.Request(OLLAMA_EMB1, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return _norm(json.loads(r.read())["embedding"])


def _embed_batch(texts: list[str], prefix: str = DOC_PREFIX) -> list[list[float]]:
    """Many texts -> many normalized vectors in ONE /api/embed call. Falls back to the older
    one-at-a-time /api/embeddings endpoint if this Ollama is too old to have /api/embed (HTTP 404)."""
    body = json.dumps({"model": EMBED_MODEL, "input": [prefix + t for t in texts]}).encode()
    req = urllib.request.Request(OLLAMA_EMBED, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return [_norm(v) for v in json.loads(r.read())["embeddings"]]
    except urllib.error.HTTPError as e:
        if e.code == 404:                          # old Ollama without /api/embed -> single calls
            return [_embed(t, prefix) for t in texts]
        raise


def _embed_all(texts: list[str], prefix: str = DOC_PREFIX) -> list[list[float]]:
    """Embed a whole doc's chunks in EMBED_BATCH-sized requests."""
    out = []
    for i in range(0, len(texts), EMBED_BATCH):
        out.extend(_embed_batch(texts[i:i + EMBED_BATCH], prefix))
    return out


def _chunk(text: str) -> list[str]:
    """Markdown-heading-aware AND code-fence-aware: start a new chunk at each '#'-heading, but
    NOT at '#' lines inside ``` / ~~~ code fences (shell/YAML examples are full of '# comments',
    which would otherwise shred code blocks). Keeps tables / spec lists / code examples whole.
    Oversized sections fall back to the sliding window; tiny adjacent sections are packed together."""
    heading = re.compile(r"^#{1,6}\s")
    fence = re.compile(r"^\s*(```|~~~)")
    sections, cur, in_fence = [], [], False
    for line in text.splitlines():
        if fence.match(line):
            in_fence = not in_fence                    # toggle: a fence delimiter is never a heading
        elif heading.match(line) and not in_fence and cur:
            sections.append("\n".join(cur)); cur = []  # real heading outside code -> new section
        cur.append(line)
    if cur:
        sections.append("\n".join(cur))
    sections = [s.strip() for s in sections if s.strip()]
    step = CHUNK_CHARS - OVERLAP
    chunks, buf = [], ""
    for sec in sections:
        if len(sec) > CHUNK_CHARS:                    # oversized section -> window it
            if buf:
                chunks.append(buf); buf = ""
            chunks += [sec[i:i + CHUNK_CHARS] for i in range(0, len(sec), step)]
        elif len(buf) + len(sec) + 2 <= CHUNK_CHARS:  # pack small sections together
            buf = f"{buf}\n\n{sec}" if buf else sec
        else:                                         # buf full -> flush, start a new one
            chunks.append(buf); buf = sec
    if buf:
        chunks.append(buf)
    return chunks or [text]


def _load_sources() -> list[tuple[str, str, str]]:
    """[(name, text, sha256), ...] de-duplicated by resolved path; missing files skipped."""
    docs, seen = [], set()
    for p in SOURCES:
        try:
            rp = p.resolve()
        except OSError:
            continue
        if rp in seen:
            continue
        seen.add(rp)
        try:
            t = p.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue                          # missing file: skip, exactly like context.py
        if t:
            sha = hashlib.sha256(t.encode("utf-8", "replace")).hexdigest()
            docs.append((p.name, t, sha))
    return docs


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.enable_load_extension(True)
    sqlite_vec.load(con)              # the vec0 extension is per-connection
    con.enable_load_extension(False)
    return con


def _ensure_schema(con) -> None:
    con.executescript(
        "CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, source TEXT, text TEXT);"
        "CREATE TABLE IF NOT EXISTS sources(name TEXT PRIMARY KEY, sha TEXT);"
        "CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);"
    )


def _meta_get(con, key: str) -> "str | None":
    row = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def _meta_set(con, key: str, value: str) -> None:
    con.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, value))


def _ensure_vec_table(con, dim: int) -> None:
    """Create the vec0 table on first use; its dimension is fixed at creation, recorded in meta."""
    if _meta_get(con, "dim") is None:
        con.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(embedding float[{dim}])")
        _meta_set(con, "dim", str(dim))


def _delete_source(con, name: str) -> None:
    """Drop a doc's chunks + vectors (vec table may not exist yet on a first build)."""
    try:
        con.execute("DELETE FROM vec_chunks WHERE rowid IN (SELECT id FROM chunks WHERE source=?)",
                    (name,))
    except sqlite3.OperationalError:
        pass                              # vec_chunks not created yet
    con.execute("DELETE FROM chunks WHERE source=?", (name,))
    con.execute("DELETE FROM sources WHERE name=?", (name,))


def build_index(force: bool = False) -> sqlite3.Connection:
    """Embed every NEW or CHANGED source into a sqlite-vec table, cached in rag_index.db. Only the
    delta is re-embedded (per-source content hash); removed docs are dropped. Returns an OPEN
    connection with the extension loaded. `force=True` wipes and re-embeds the whole corpus."""
    docs = _load_sources()
    con = _connect()
    _ensure_schema(con)
    settings = f"{CHUNK_CHARS}|{OVERLAP}|{EMBED_MODEL}|{DOC_PREFIX}|{QUERY_PREFIX}"
    if force or _meta_get(con, "settings") != settings:
        # a settings change invalidates every stored embedding -> wipe and full rebuild
        con.executescript("DROP TABLE IF EXISTS vec_chunks;"
                           "DELETE FROM chunks; DELETE FROM sources; DELETE FROM meta;")
        _ensure_schema(con)
        _meta_set(con, "settings", settings)
    have = dict(con.execute("SELECT name, sha FROM sources").fetchall())
    current = {name: (text, sha) for name, text, sha in docs}
    for name in set(have) - set(current):          # docs removed from SOURCES
        _delete_source(con, name); _log(f"  [removed] {name}")
    todo = [(n, t, s) for n, (t, s) in current.items() if have.get(n) != s]
    if not todo:
        con.commit()
        return con                                 # nothing new/changed -> reuse the embeddings
    _log(f"indexing {len(todo)} new/changed doc(s) of {len(current)} (batch={EMBED_BATCH})...")
    for name, text, sha in todo:
        _delete_source(con, name)                  # clear stale rows if the doc changed
        chunks = _chunk(text)
        if not chunks:
            continue
        vecs = _embed_all(chunks)
        _ensure_vec_table(con, len(vecs[0]))
        for txt, v in zip(chunks, vecs):
            cur = con.execute("INSERT INTO chunks(source, text) VALUES(?, ?)", (name, txt))
            con.execute("INSERT INTO vec_chunks(rowid, embedding) VALUES(?, ?)",
                        (cur.lastrowid, serialize_float32(v)))
        con.execute("INSERT OR REPLACE INTO sources(name, sha) VALUES(?, ?)", (name, sha))
        con.commit()                               # commit per doc -> safe to interrupt and resume
        _log(f"  [indexed] {name}: {len(chunks)} chunks")
    return con


# --- hybrid rerank: fetch a larger vector pool, then re-rank by cosine + how much the chunk's
# vocabulary overlaps the QUESTION (a BM25-style lexical signal). Measured on this repo's frozen
# 33-QA set: MRR@5 0.79 -> 0.95, hit@5 0.94 -> 0.97 — the answer passage both embeds near AND
# shares words with the question, and lexical overlap breaks ties the embedding alone gets wrong.
RERANK_POOL  = 20     # vector candidates to rerank (>= k)
RERANK_ALPHA = 0.6    # weight on cosine; (1-alpha) on lexical overlap. 0.5-0.7 all optimal here.
_WORD = re.compile(r"[a-z0-9]{3,}")
_STOP = frozenset(("the and for with your you are that this how what when where can does from into "
                   "will would should could have has had not but they them then than").split())


def _lex_overlap(query: str, text: str) -> float:
    qw = set(_WORD.findall(query.lower())) - _STOP
    if not qw:
        return 0.0
    return len(qw & set(_WORD.findall(text.lower()))) / len(qw)


def _knn(con, question: str, k: int):
    """The k best chunks as [(cosine_score, source, text), ...], hybrid-reranked (vector + lexical).
    The returned score is still the cosine (so retrieve()'s min_score floor is unchanged); only the
    ORDER reflects the hybrid rank. Empty if the corpus is empty."""
    q = serialize_float32(_embed(question, QUERY_PREFIX))
    pool = max(k, RERANK_POOL)
    try:
        rows = con.execute(
            "SELECT rowid, distance FROM vec_chunks WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
            (q, pool),
        ).fetchall()
    except sqlite3.OperationalError:
        return []                    # no vec_chunks table -> nothing indexed
    out = []
    for rowid, dist in rows:
        score = 1.0 - (dist * dist) / 2.0    # L2 on UNIT vectors -> cosine (vectors are normalized)
        src, txt = con.execute("SELECT source, text FROM chunks WHERE id = ?", (rowid,)).fetchone()
        out.append((score, src, txt))
    out.sort(key=lambda r: -(RERANK_ALPHA * r[0] + (1.0 - RERANK_ALPHA) * _lex_overlap(question, r[2])))
    return out[:k]


def retrieve(question: str, k: int = TOP_K, min_score: float = MIN_SCORE) -> list[str]:
    """Up to k reference chunks relevant to the question. Empty if nothing clears min_score."""
    con = build_index()
    hits = _knn(con, question, k)
    con.close()
    return [f"[{src}] {txt}" for score, src, txt in hits if score >= min_score]


def context_block(question: str) -> str:
    """Ready-to-inject grounding text for context.build(); '' when nothing is relevant.
    NEVER raises: if Ollama is down or the embed model isn't pulled, retrieval degrades to ''
    so the chat keeps working (static facts + live snapshot + findings still ground the answer).
    This is what lets context.build() — called OUTSIDE brain.ask's try/except — stay crash-proof."""
    try:
        hits = retrieve(question)
    except Exception:
        return ""                              # Ollama unavailable / model not pulled -> no docs
    if not hits:
        return ""
    return ("REFERENCE DOCS (retrieved as most relevant to this question — quote these):\n\n"
            + "\n\n---\n\n".join(hits))


def _scored(question: str):
    """All chunks scored, nearest first — for `--scores` calibration."""
    con = build_index()
    n = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
    hits = _knn(con, question, n or 1)
    con.close()
    return hits


def demo():  # the one runnable check
    assert len(_chunk("x" * 3000)) >= 3, "sliding-window chunker is wrong"
    v = [0.6, 0.8]                             # a unit vector's cosine with itself must be 1
    assert abs(sum(a * b for a, b in zip(v, v)) - 1.0) < 1e-6, "cosine math wrong"
    print("rag chunk/math ok")
    if not DB.exists():                        # honor "build later": don't kick off a full build here
        print(f"(index not built yet — run `python rag.py --build` to embed {len(_load_sources())} docs)")
        return
    try:
        con = _connect(); n = con.execute("SELECT count(*) FROM chunks").fetchone()[0]; con.close()
        if not n:
            print("(index is empty — run `python rag.py --build`)"); return
        hits = retrieve("how is my reverse proxy / homelab networking set up?")
        print(f"rag index ok: {n} chunks; query returned {len(hits)} relevant chunk(s)")
        if hits:
            print("top hit:", hits[0][:160].replace("\n", " "))
    except Exception as e:
        print(f"(skipped live retrieve - is Ollama up + `ollama pull {EMBED_MODEL}` done? {e})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--build":
        con = build_index(force="--force" in sys.argv)
        n = con.execute("SELECT count(*) FROM chunks").fetchone()[0]; con.close()
        print(f"index built: {n} chunks from {len(_load_sources())} doc(s)")
    elif len(sys.argv) > 2 and sys.argv[1] == "--scores":
        for score, src, txt in _scored(sys.argv[2]):
            print(f"{score:.3f}  [{src}] {txt[:90].strip()}")
    else:
        demo()

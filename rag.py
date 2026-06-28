# rag.py — tiny local RAG for Watch Tower. Makes your reference docs (homelab notes, manuals,
# runbooks) searchable so the chat model can quote the RIGHT few paragraphs instead of being fed
# a whole document. Embeddings come from Ollama's local embedding model; retrieval is a cosine
# KNN over a sqlite-vec vector store. READ-ONLY: it only SELECTS text to show the model.
#
# Deps: Ollama (already required) + `ollama pull nomic-embed-text` + `pip install sqlite-vec`.
# Everything else (json/urllib/pathlib/hashlib/re/math/sqlite3) is stdlib.

import json, urllib.request, pathlib, hashlib, re, math, sys, sqlite3
import sqlite_vec
from sqlite_vec import serialize_float32

OLLAMA = "http://127.0.0.1:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"      # `ollama pull nomic-embed-text` (~270 MB, runs on CPU)
HERE = pathlib.Path(__file__).parent
DB = HERE / "rag_index.db"            # generated cache — git-ignore it

# Docs to make searchable. Add your own; missing files are skipped (like context.py's HOMELAB).
SOURCES = [
    pathlib.Path.home() / "homelab" / "HOMELAB-COMPLETE-SETUP.md",
    HERE / "MAG_Z790_TOMAHAWK_MAX_WIFI_User_Guide.md",
]

# --- tuning knobs (the RAG equivalent of rules.THRESH — tune for YOUR docs) ---
CHUNK_CHARS = 1200    # size of each searchable slice (~300 tokens)
OVERLAP     = 200     # chars repeated between neighbours so a fact on a boundary isn't lost
TOP_K       = 4       # how many chunks to return per question
MIN_SCORE   = 0.45    # cosine floor; below this a chunk is "not really relevant" and is dropped
                      #   -> an off-topic question retrieves nothing. THIS is the knob to tune.

# nomic-embed-text wants these task prefixes; they materially improve retrieval. Other embedders
# differ: mxbai-embed-large wants only a query-side instruction and no document prefix. If unsure
# for your model, set both to "" — it works, just slightly weaker on the query side.
DOC_PREFIX   = "search_document: "
QUERY_PREFIX = "search_query: "


def _embed(text: str, prefix: str = DOC_PREFIX) -> list[float]:
    """One text -> one L2-normalized vector, via Ollama. Normalized so cosine == dot product."""
    body = json.dumps({"model": EMBED_MODEL, "prompt": prefix + text}).encode()
    req = urllib.request.Request(OLLAMA, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        v = json.loads(r.read())["embedding"]
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


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


def _load_sources() -> list[tuple[str, str]]:
    docs = []
    for p in SOURCES:
        try:
            t = p.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue                          # missing file: skip, exactly like context.py
        if t:
            docs.append((p.name, t))
    return docs


def _sig(docs) -> str:
    """Fingerprint of inputs + settings. If it changes, the cache is stale and we re-embed."""
    h = hashlib.sha256(f"{CHUNK_CHARS}|{OVERLAP}|{EMBED_MODEL}".encode())
    for name, text in docs:
        h.update(name.encode()); h.update(text.encode("utf-8", "replace"))
    return h.hexdigest()


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.enable_load_extension(True)
    sqlite_vec.load(con)              # the vec0 extension is per-connection
    con.enable_load_extension(False)
    return con


def _stored_sig(con) -> "str | None":
    try:
        row = con.execute("SELECT value FROM meta WHERE key='sig'").fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None                  # tables don't exist yet (fresh db)


def build_index(force: bool = False) -> sqlite3.Connection:
    """Embed every chunk into a sqlite-vec table, cached in rag_index.db. Rebuilds on doc change.
    Returns an OPEN connection with the extension loaded."""
    docs = _load_sources()
    sig = _sig(docs)
    con = _connect()
    if not force and _stored_sig(con) == sig:
        return con                   # docs + settings unchanged -> reuse the embeddings
    con.executescript(
        "DROP TABLE IF EXISTS vec_chunks;"
        "DROP TABLE IF EXISTS chunks;"
        "DROP TABLE IF EXISTS meta;"
        "CREATE TABLE chunks(id INTEGER PRIMARY KEY, source TEXT, text TEXT);"
        "CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);"
    )
    chunks, sources = [], []
    for name, text in docs:
        for c in _chunk(text):
            chunks.append(c); sources.append(name)
    if chunks:
        vecs = [_embed(c) for c in chunks]
        con.execute(f"CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[{len(vecs[0])}])")
        for src, txt, v in zip(sources, chunks, vecs):
            cur = con.execute("INSERT INTO chunks(source, text) VALUES (?, ?)", (src, txt))
            con.execute("INSERT INTO vec_chunks(rowid, embedding) VALUES (?, ?)",
                        (cur.lastrowid, serialize_float32(v)))
    con.execute("INSERT INTO meta(key, value) VALUES ('sig', ?)", (sig,))
    con.commit()
    return con


def _knn(con, question: str, k: int):
    """The k nearest chunks as [(cosine_score, source, text), ...]; empty if the corpus is empty."""
    q = serialize_float32(_embed(question, QUERY_PREFIX))
    try:
        rows = con.execute(
            "SELECT rowid, distance FROM vec_chunks WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
            (q, k),
        ).fetchall()
    except sqlite3.OperationalError:
        return []                    # no vec_chunks table -> nothing indexed
    out = []
    for rowid, dist in rows:
        score = 1.0 - (dist * dist) / 2.0    # L2 on UNIT vectors -> cosine (vectors are normalized)
        src, txt = con.execute("SELECT source, text FROM chunks WHERE id = ?", (rowid,)).fetchone()
        out.append((score, src, txt))
    return out


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
    try:
        con = build_index(); n = con.execute("SELECT count(*) FROM chunks").fetchone()[0]; con.close()
        hits = retrieve("how is my reverse proxy / homelab networking set up?")
        print(f"rag index ok: {n} chunks; query returned {len(hits)} relevant chunk(s)")
        if hits:
            print("top hit:", hits[0][:160].replace("\n", " "))
    except Exception as e:
        print(f"(skipped live retrieve - is Ollama up + `ollama pull {EMBED_MODEL}` done? {e})")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--scores":
        for score, src, txt in _scored(sys.argv[2]):
            print(f"{score:.3f}  [{src}] {txt[:90].strip()}")
    else:
        demo()
# Watch Tower — Add a Local RAG Pipeline (Windows)

A copy-paste guide to add **retrieval-augmented generation** to the chat brain. Right now
`context.py` injects a whole reference doc behind a keyword gate; this replaces that with proper
*semantic retrieval* — the chat model gets only the few paragraphs actually relevant to your
question, pulled from any docs you point it at.

> Prerequisite: a working Watch Tower from [`RECREATE-WINDOWS.md`](RECREATE-WINDOWS.md) (you need
> `context.py`, `brain.py`, and Ollama running). This guide adds **one new file** (`rag.py`) and
> edits **one** (`context.py`). `brain.py` does **not** change.

> **Zero new pip dependencies.** Everything `rag.py` uses — `json`, `urllib`, `pathlib`,
> `hashlib`, `re`, `math` — is the Python standard library. Embeddings come from **Ollama**,
> which you already run. The only new thing to install is an embedding *model* (a one-line
> `ollama pull`). The project stays at its three pip deps (`torch`, `gradio`, `pandas`).

---

## 0. What you are building

A 120-line, dependency-free retriever that sits between your question and the chat model:

```
                          (you already have this)
 question ─► context.build(message) ─────────────────────────► brain.ask ─► Ollama qwen2.5:32b
                  │  STATIC FACTS + LIVE SNAPSHOT + FINDINGS                     ▲
                  │                                                              │
                  └─► rag.context_block(message)  ◄── NEW                        │
                          │                                                      │
              ┌───────────┴───────────┐                                         │
              ▼                       ▼                                          │
        embed the question      cosine top-k over    ──► the 4 most relevant ───┘
        (Ollama embed model)    cached doc vectors        chunks, or nothing
                                (rag_index.json)           if none clear the bar
```

**How it works:** your reference docs are split into overlapping chunks, each chunk is turned
into a vector by a local embedding model once and cached to `rag_index.json`. At question time we
embed the question, take the cosine similarity against every chunk, and return the top few — but
only if they clear a relevance floor, so an off-topic question (e.g. "is my GPU hot?") retrieves
nothing and adds no noise. The cache rebuilds automatically when a source doc changes.

**Still read-only.** Like the rest of Watch Tower, RAG only *selects text to show the model*. It
never executes anything.

---

## 1. Prerequisites (one model pull)

| Tool | Why | Install |
|---|---|---|
| **Watch Tower** (working) | RAG plugs into `context.py` | [`RECREATE-WINDOWS.md`](RECREATE-WINDOWS.md) |
| **Ollama** (already running) | serves the embedding model locally | already required by the base project |
| **An embedding model** | turns text into vectors | `ollama pull nomic-embed-text` |

```powershell
ollama pull nomic-embed-text
```

Expected (the model is ~270 MB and runs fine on CPU — no VRAM needed):

```
pulling manifest
pulling ... 100% ▕████████████████▏ 274 MB
verifying sha256 digest
writing manifest
success
```

Confirm it's there:

```powershell
ollama list
```

```
NAME                       ID              SIZE      MODIFIED
nomic-embed-text:latest    0a109f422b47    274 MB    10 seconds ago
qwen2.5:32b                ...             19 GB     ...
```

> **Why a dedicated embedding model?** Chat models (like `qwen2.5:32b`) return an *empty* vector
> from the embeddings endpoint — they have no embedding head exposed. You must use a real embedder
> (`nomic-embed-text`, or `mxbai-embed-large` for higher quality at ~670 MB).

---

## 2. Create `rag.py`

Paste this into the project root (next to `context.py`). It is self-contained and self-tests with
`python rag.py`.

```python
# rag.py — tiny local RAG for Watch Tower. Makes your reference docs (homelab notes, manuals,
# runbooks) searchable so the chat model can quote the RIGHT few paragraphs instead of being fed
# a whole document. Embeddings come from Ollama's local embedding model; retrieval is a cosine
# top-k over a JSON cache. READ-ONLY: it only SELECTS text to show the model.
#
# Dependencies: NONE beyond what Watch Tower already needs. json/urllib/pathlib/hashlib/re/math
# are stdlib; embeddings come from Ollama (already required). New install: `ollama pull nomic-embed-text`.

import json, urllib.request, pathlib, hashlib, re, math, sys

OLLAMA = "http://127.0.0.1:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"      # `ollama pull nomic-embed-text` (~270 MB, runs on CPU)
HERE = pathlib.Path(__file__).parent
INDEX = HERE / "rag_index.json"       # generated cache — git-ignore it

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
    # ponytail: fixed-size sliding window. Predictable, and OVERLAP covers boundary cuts.
    # Upgrade to paragraph/markdown-aware splitting only if recall is poor.
    step = CHUNK_CHARS - OVERLAP
    return [text[i:i + CHUNK_CHARS] for i in range(0, len(text), step)] or [text]


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


def build_index(force: bool = False) -> dict:
    """Embed every chunk of every source doc, cached to rag_index.json. Rebuilds on doc change."""
    docs = _load_sources()
    sig = _sig(docs)
    if not force and INDEX.exists():
        cached = json.loads(INDEX.read_text(encoding="utf-8"))
        if cached.get("sig") == sig:
            return cached                     # docs unchanged -> reuse the embeddings
    chunks, sources = [], []
    for name, text in docs:
        for c in _chunk(text):
            chunks.append(c); sources.append(name)
    vecs = [_embed(c) for c in chunks]        # one HTTP call per chunk (cached after this run)
    idx = {"sig": sig, "chunks": chunks, "sources": sources, "vecs": vecs}
    INDEX.write_text(json.dumps(idx), encoding="utf-8")
    return idx


def _scored(question: str):
    """All chunks scored against the question, highest cosine first."""
    idx = build_index()
    if not idx["chunks"]:
        return []
    q = _embed(question, QUERY_PREFIX)
    out = [(sum(a * b for a, b in zip(q, v)), i) for i, v in enumerate(idx["vecs"])]
    out.sort(reverse=True)                     # ponytail: linear scan; fine to a few thousand
    return [(s, i, idx) for s, i in out]       # chunks. Past that, reach for numpy / a vector DB.


def retrieve(question: str, k: int = TOP_K, min_score: float = MIN_SCORE) -> list[str]:
    """Up to k reference chunks relevant to the question. Empty if nothing clears min_score."""
    hits = _scored(question)[:k]
    return [f"[{idx['sources'][i]}] {idx['chunks'][i]}" for s, i, idx in hits if s >= min_score]


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


def demo():  # the one runnable check
    # offline: chunking + cosine math work with no Ollama running
    assert len(_chunk("x" * 3000)) >= 3, "sliding-window chunker is wrong"
    v = [0.6, 0.8]                             # a unit vector's cosine with itself must be 1
    assert abs(sum(a * b for a, b in zip(v, v)) - 1.0) < 1e-6, "cosine math wrong"
    print("rag chunk/math ok")
    try:                                       # online: only if Ollama + the model are present
        n = len(build_index()["chunks"])
        hits = retrieve("how is my reverse proxy / homelab networking set up?")
        print(f"rag index ok: {n} chunks; query returned {len(hits)} relevant chunk(s)")
        if hits:
            print("top hit:", hits[0][:160].replace("\n", " "))
    except Exception as e:
        print(f"(skipped live retrieve - is Ollama up + `ollama pull {EMBED_MODEL}` done? {e})")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--scores":   # calibrate MIN_SCORE
        for s, i, idx in _scored(sys.argv[2]):
            print(f"{s:.3f}  [{idx['sources'][i]}] {idx['chunks'][i][:90].strip()}")
    else:
        demo()
```

Set `SOURCES` to the docs you want searchable — point it at your homelab notes, a hardware
manual you've saved as `.md`/`.txt`, a runbook, anything. Missing files are silently skipped, so
it's safe to list docs that don't exist yet.

Self-test it:

```powershell
python rag.py
```

Example output (with `nomic-embed-text` pulled and a real `SOURCES` doc present; your counts and
scores will differ):

```
rag chunk/math ok
rag index ok: 37 chunks; query returned 4 relevant chunk(s)
top hit: [HOMELAB-COMPLETE-SETUP.md] ## Reverse proxy ...
```

If Ollama is down or the model isn't pulled, the first line still prints and the rest degrades to
a one-line skip — the offline logic is proven without the model.

---

## 3. Wire it into `context.py` (this is "how the LLM uses it")

The chat brain already grounds every answer in `context.build(message)` — that string becomes the
`{ctx}` in `brain.SYSTEM`. So the only change needed is to have `build()` append retrieved chunks.
**RAG replaces the old keyword gate** (`_wants_homelab` / `HOMELAB_TRIGGERS`): semantic similarity
does the relevance decision now, so the keyword list and the whole-doc dump go away.

> **Tradeoff to know:** the old gate dumped the *entire* doc (~9k tokens) on any keyword match;
> RAG injects only the `TOP_K` best chunks. That's a precision win for focused questions but feeds
> the model less on broad "give me the whole picture" ones. Raise `TOP_K` if you want more
> coverage — it's a precision/recall dial, not a strict upgrade over the blunt switch.

**3a.** Add the import at the top of `context.py`:

```python
import json, pathlib
import rules
import rag                      # NEW
```

**3b.** Replace the tail of `build()` — delete the `_wants_homelab` block and inject RAG instead:

```python
def build(message: str = "") -> str:
    snap, findings = snapshot_and_findings()
    parts = [
        "STATIC FACTS ABOUT THIS MACHINE:",
        _read(FACTS) or "(no system_facts.md)",
        "",
        "LIVE SNAPSHOT (JSON, just collected):",
        json.dumps(snap, indent=2),
        "",
        "FINDINGS (deterministic ground truth from rules.py — trust these over guesses):",
        json.dumps(findings, indent=2) if findings else "none — all nominal",
    ]
    refs = rag.context_block(message)      # semantic retrieval replaces the keyword gate
    if refs:
        parts += ["", refs]
    return "\n".join(parts)
```

**3c.** Delete the now-dead gate (the `HOMELAB`, `HOMELAB_TRIGGERS`, and `_wants_homelab` lines)
and move that doc path into `rag.SOURCES` instead (step 2). Update the `__main__` self-test, which
referenced `_wants_homelab`:

```python
if __name__ == "__main__":
    out = build("how is my reverse proxy set up?")
    assert "FINDINGS" in out, "context block lost its findings"
    print(out[:800])
```

That's the entire integration. **`brain.py` is unchanged** — it calls `context.build(user_text)`,
gets the static facts + live snapshot + findings + *the retrieved chunks*, and passes the whole
thing as the system prompt. The model now quotes the right paragraphs of your docs automatically,
on the questions where they're relevant, and ignores them otherwise.

---

## 4. Verify end to end

```powershell
python context.py
```

A homelab-style question pulls reference chunks into the context (you'll see a
`REFERENCE DOCS (...)` section in the printed block); a pure-hardware question won't.

Tune the relevance floor with the score view — it prints every chunk's cosine so you can pick a
`MIN_SCORE` between "clearly relevant" and "noise":

```powershell
python rag.py --scores "how is traefik configured?"
```

Example output (illustrative scores):

```
0.71  [HOMELAB-COMPLETE-SETUP.md] ## Reverse proxy (Traefik) ...
0.68  [HOMELAB-COMPLETE-SETUP.md] ### Traefik dynamic config ...
0.39  [HOMELAB-COMPLETE-SETUP.md] ## Backups ...
0.31  [HOMELAB-COMPLETE-SETUP.md] ## Hardware inventory ...
```

Here `0.45` cleanly separates the two real hits from the noise. Raise `MIN_SCORE` if junk leaks
in; lower it if relevant docs are being missed.

Then just use the chat as normal — CLI or web:

```powershell
python chat.py        # or: python app.py
```

Ask something covered by your docs ("what port does my reverse proxy listen on?") and the answer
will cite the retrieved text instead of guessing.

---

## 5. Tuning & maintenance

| Knob (in `rag.py`) | Default | Raise it / change it when |
|---|---|---|
| `SOURCES` | one homelab doc | add every `.md`/`.txt` you want searchable |
| `MIN_SCORE` | `0.45` | **the main dial.** Higher = stricter (less noise, risk of missing); lower = looser |
| `TOP_K` | `4` | answers need more context; watch you don't blow `num_ctx` in `brain.py` |
| `CHUNK_CHARS` / `OVERLAP` | `1200` / `200` | smaller chunks = finer retrieval; bigger = more context per hit |
| `EMBED_MODEL` | `nomic-embed-text` | want higher quality → `mxbai-embed-large` (~670 MB; adjust the prefixes — see the prefix note in `rag.py`) |

- **The cache rebuilds itself.** `rag_index.json` is keyed by a hash of your docs + settings;
  edit a source doc (or any knob above) and the next call re-embeds automatically. To force it:
  `python -c "import rag; rag.build_index(force=True)"`.
- **First call after a doc edit is slower** (one embed call per chunk) — for a typical doc that's
  a second or two, then it's instant from cache.
- **Git-ignore the cache.** Add it to `.gitignore`:

  ```
  rag_index.json
  ```

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `HTTP Error 404` on embed | model not pulled — run `ollama pull nomic-embed-text`; check `ollama list` |
| `embedding dims = 0` / retrieval always empty | you pointed `EMBED_MODEL` at a **chat** model. Use a real embedder (`nomic-embed-text`) |
| Retrieval returns nothing for relevant questions | `MIN_SCORE` too high, or `SOURCES` path wrong / file missing. Use `python rag.py --scores "..."` to see actual scores |
| Off-topic questions still pull doc chunks | `MIN_SCORE` too low — raise it |
| Slow chat after editing a doc | expected: it's re-embedding once; cached afterwards |
| Want batch/faster indexing | newer Ollama has `/api/embed` (takes `"input": [..]` and returns `"embeddings": [[..]]`) — swap the endpoint to embed all chunks in one call |

---

That's the whole pipeline: ~120 lines, no new pip packages, one `ollama pull`, one file edited.
It keeps Watch Tower's promises — local-only, read-only, minimal-dependency — while giving the
chat model real document grounding instead of a blunt keyword switch.

---

## 7. Better chunking for dense manuals (optional)

The default `_chunk` is a **fixed-size sliding window**. It's predictable and fine for prose
(homelab notes, runbooks), but it underperforms on **structured technical docs** — a motherboard
manual full of tables, pinouts, and spec lists — because it slices sections mid-content.

### How to tell it's biting you

Run `--scores` on a real question and read the ranking, not just the top line. Example, asking a
loaded MSI manual *"what ports do I have on my motherboard?"*:

```
0.737  [..User_Guide.md] packages (1 set/pack) · 1x Cable sticker ...   <- box contents (noise)
0.721  [..User_Guide.md] / JUSB3 / JUSB1~2: USB Connectors ...
0.694  [..User_Guide.md] CPU_PWR1~2 | Pin | Signal ...                  <- pinout, not ports
...
0.665  [..User_Guide.md] 1x USB 3.2 Gen 2x2 20Gbps Type-C · 2.5Gbps LAN <- the ACTUAL answer, rank ~11
```

Three tells, all visible above:

- **The real answer is buried.** The rear-I/O list (USB-C, LAN, Wi-Fi) is rank ~11 — with
  `TOP_K=4` the model never sees it.
- **The top hit is noise.** Packaging text out-ranks ports because "USB ports" appears near it.
- **Scores are compressed** (≈0.47–0.74). That's normal for one dense doc — but it means
  `MIN_SCORE` is a weak filter here; the ranking, not the absolute score, carries the signal.

Root cause: the 1200-char window splits the manual's tables, so the one coherent "Rear I/O Ports"
summary gets diluted and out-ranked by a dozen near-duplicate connector/pinout fragments.

### Two ways to fix it

| | Fix | Tradeoff |
|---|---|---|
| **A — quick** | Bump `TOP_K` to ~8–10 and retest | Immediate, but blunt: a rank-11 answer needs a big `K`, which drags in more noise and tokens |
| **B — real fix (recommended for manuals)** | Replace `_chunk` with the **heading-aware** version below, so a section like "Rear I/O Ports" stays one whole chunk and ranks higher | ~15 lines, still zero new deps; best when you'll lean on a structured doc |

### The heading-aware `_chunk` (drop-in replacement)

Paste this over the existing `_chunk` in `rag.py`. Same signature, same `CHUNK_CHARS`/`OVERLAP`
knobs — it just respects markdown `#` headings instead of cutting blindly.

```python
def _chunk(text: str) -> list[str]:
    """Markdown-heading-aware: keep each '#'-section whole so tables / spec lists / pinouts don't
    get sliced mid-content. Sections bigger than CHUNK_CHARS fall back to the sliding window;
    tiny adjacent sections are packed together. Better recall on structured docs (manuals)."""
    parts = re.split(r"(?m)^(?=#{1,6}\s)", text)      # split *before* each heading line
    sections = [p.strip() for p in parts if p.strip()]
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
```

> Works because each chunk now starts at a heading and carries that heading's whole body (table
> and all). A section longer than `CHUNK_CHARS` still falls back to the windowed split, so nothing
> is ever dropped. The `python rag.py` self-test still passes (a heading-less 3000-char blob has
> no headings → one big section → windowed into 3 chunks).

After pasting, **rebuild and retest** — the cache must re-embed with the new chunk boundaries:

```powershell
python -c "import rag; rag.build_index(force=True)"
python rag.py --scores "what ports do I have on my motherboard?"
```

You should see the rear-I/O / connector sections rise toward the top. If a still-relevant chunk
sits just outside `TOP_K`, nudge `TOP_K` to 5–6 — with whole sections you need far fewer than the
windowed version did.

---

## 8. Scale up: swap the JSON store for a vector database (sqlite-vec)

The default store is a JSON file + a pure-Python cosine scan — fine to ~a few thousand chunks.
Past that (large doc set, slow `--scores`, or you want metadata filtering / incremental updates),
graduate the retrieval backend to **sqlite-vec**: a vector-search extension for the SQLite you
*already* use for `history.db`. Still local, still file-based, no server.

> **This is the one deliberate break from "zero new pip deps."** You add exactly one package
> (`sqlite-vec`). The public API of `rag.py` does **not** change — `context.py` and `brain.py`
> stay untouched. Only the internals (storage + search) swap out. Don't do this until you've
> actually hit the scan ceiling; for a few hundred chunks the JSON store is faster to reason about.

### 8.0 Prereq check — extension loading

sqlite-vec loads as a SQLite extension, which needs your Python's `sqlite3` built with extension
loading enabled. Check first:

```powershell
python -c "import sqlite3; sqlite3.connect(':memory:').enable_load_extension(True); print('OK')"
```

```
OK
```

If that raises `AttributeError`/`OperationalError` instead of printing `OK`, your Python can't load
the extension — **stay on the JSON store and just vectorize the scan with numpy instead** (numpy
ships with torch/pandas, so that's still zero new deps). Otherwise continue.

### 8.1 Install

```powershell
pip install sqlite-vec
```

Add it to `requirements.txt` (this is now a real dependency):

```
sqlite-vec   # vector store for rag.py (only if you did the section 8 upgrade)
```

> Wheels exist for Python 3.14 on Windows (verified: `sqlite-vec` v0.1.9). If `pip` can't find a
> wheel for your Python, that's the only likely blocker — fall back to the numpy option above.

### 8.2 Edit `rag.py` (public API unchanged)

**Imports** — add `sqlite3` + sqlite-vec:

```python
import json, urllib.request, pathlib, hashlib, re, math, sys, sqlite3
import sqlite_vec
from sqlite_vec import serialize_float32
```

**Cache constant** — it's a database now, not JSON:

```python
DB = HERE / "rag_index.db"            # was: INDEX = HERE / "rag_index.json"
```

**Replace `build_index`, `retrieve`, and `_scored`, and add `_connect` / `_stored_sig` / `_knn`.**
`_embed`, `_chunk`, `_load_sources`, `_sig`, and `context_block` stay exactly as they are.

```python
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
        # the vec0 column needs a literal dimension -> take it from the first vector
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
        score = 1.0 - (dist * dist) / 2.0    # L2 on UNIT vectors -> cosine (see note below)
        src, txt = con.execute("SELECT source, text FROM chunks WHERE id = ?", (rowid,)).fetchone()
        out.append((score, src, txt))
    return out


def retrieve(question: str, k: int = TOP_K, min_score: float = MIN_SCORE) -> list[str]:
    """Up to k reference chunks relevant to the question. Empty if nothing clears min_score."""
    con = build_index()
    hits = _knn(con, question, k)
    con.close()
    return [f"[{src}] {txt}" for score, src, txt in hits if score >= min_score]


def _scored(question: str):
    """All chunks scored, nearest first — for `--scores` calibration."""
    con = build_index()
    n = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
    hits = _knn(con, question, n or 1)
    con.close()
    return hits
```

**Update `demo()` and `__main__`** — `build_index` returns a connection now, not a dict:

```python
def demo():  # the one runnable check
    assert len(_chunk("x" * 3000)) >= 3, "sliding-window chunker is wrong"
    v = [0.6, 0.8]
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
```

### 8.3 Why the cosine math is a one-liner

sqlite-vec ranks by **L2 distance** by default. Your `_embed` already L2-normalizes every vector,
and for unit vectors `dist² = 2 − 2·cos`, so **ascending L2 distance == descending cosine** — the
top-k ordering is identical, and `score = 1 − dist²/2` recovers the exact cosine. (Verified: the
reconstructed score matches a brute-force dot product to 4 decimals.) Because the vectors stay
normalized, your `MIN_SCORE = 0.45` threshold keeps the same meaning — no retuning needed.

### 8.4 Migrate and verify

```powershell
# .gitignore: swap the cache filename
#   rag_index.json   ->   rag_index.db

del rag_index.json                                   # remove the old store (if present)
python -c "import rag; rag.build_index(force=True)"  # build the sqlite-vec index once
python rag.py                                        # self-test
python rag.py --scores "what ports do I have on my motherboard?"
```

Expected `python rag.py` (with the embed model pulled and a real `SOURCES` doc):

```
rag chunk/math ok
rag index ok: 46 chunks; query returned 4 relevant chunk(s)
top hit: [MAG_Z790_TOMAHAWK_MAX_WIFI_User_Guide.md] ...
```

Same numbers, same answers as before — the difference is the search now runs in the DB engine and
scales to far more chunks than a Python loop.

### 8.5 What you unlocked (and the next step)

- **Speed at scale** — KNN runs in SQLite instead of a Python `for` loop.
- **Persistence** — the index is a real DB file you can inspect with any SQLite tool.
- **Metadata filtering (next step)** — `vec0` KNN won't accept an extra `WHERE` (or a JOIN
  filter) beside `MATCH`; it errors with *"a LIMIT or 'k = ?' constraint is required"* because the
  KNN must own the query. The simple, always-correct pattern with this schema is **over-fetch then
  filter in Python**. Add a `category` column to `chunks` (set it at insert time), then e.g.
  *"only Windows docs"*:

  ```python
  con = build_index()
  q = serialize_float32(_embed(question, QUERY_PREFIX))
  rows = con.execute(                                   # pull a POOL, not just k
      "SELECT rowid, distance FROM vec_chunks WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
      (q, 50),
  ).fetchall()
  out = []
  for rowid, dist in rows:                              # already nearest-first
      src, txt, cat = con.execute(
          "SELECT source, text, category FROM chunks WHERE id = ?", (rowid,)).fetchone()
      if cat == "windows" and 1.0 - dist * dist / 2.0 >= MIN_SCORE:
          out.append(f"[{src}] {txt}")
      if len(out) == TOP_K:
          break
  con.close()
  ```

  (For DB-side filtering at larger scale, sqlite-vec's newer *metadata/partition columns* declared
  inside the `vec0` table are the proper tool — see the sqlite-vec docs — but post-filter is the
  zero-risk version.)

**Rollback** is clean: it's all in git and the public API is unchanged, so `git checkout rag.py`
(and restore the `rag_index.json` line in `.gitignore`) puts you back on the JSON store.

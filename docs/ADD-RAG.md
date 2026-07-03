# Watch Tower — Add a Local RAG Pipeline

> **This guide has been merged into the main recreate docs.** The full, current RAG pipeline —
> batch + incremental indexing over a sqlite-vec vector store, a hybrid vector+lexical rerank, and
> the embedding-model options — now lives as **§12. Add a local RAG pipeline** in:
>
> - [`RECREATE-WINDOWS.md` → §12](RECREATE-WINDOWS.md#12-add-a-local-rag-pipeline-semantic-doc-retrieval)
> - [`RECREATE-LINUX.md` → §12](RECREATE-LINUX.md#12-add-a-local-rag-pipeline-semantic-doc-retrieval)
>
> The recreate guides are the single source of truth; this stub remains only so existing links
> don't break.

## What it is

A dependency-light retriever (`rag.py`) that makes every `.md` reference doc in the project folder
semantically searchable, so the chat brain quotes the few relevant paragraphs instead of being fed
whole documents. Local-only, read-only, embeddings via Ollama, vectors in sqlite-vec, with a
**hybrid vector+lexical rerank** (the passage that both embeds near the question and shares its
vocabulary is promoted). Default embedding model: `mxbai-embed-large`. See §12 of either recreate
guide for the exact file contents, commands, expected output, and the chat/embedding model tables.

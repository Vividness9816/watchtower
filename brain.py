### brain.py — the chatbot brain. Qwen2.5-32B via Ollama, grounded in the live system state from context.py. READ-ONLY: the model is told it cannot act, and nothing it returns is ever executed — its output is text shown to a human. ###

import json, urllib.request, urllib.error
import context

OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:32b"            # Q4_K_M by default; fits the <GPU>'s 32GB VRAM

SYSTEM = """You are a hands-on hardware-diagnostics and troubleshooting expert for THIS
specific Windows 11 PC. You answer questions about its health and tell the user EXACTLY what
to do — as concrete, copy-pasteable steps.

How to answer — ALWAYS:
- Give numbered, step-by-step instructions. Assume the user copies and runs each step.
- For EVERY command state all four: (1) the shell — PowerShell; (2) the exact command in a code
  block; (3) the folder to run it from — give the literal `cd` command when it matters; (4)
  whether it needs an ELEVATED (Administrator) shell. If it does, say so first and tell them to
  open Windows Terminal / PowerShell "as Administrator" before that step.
- End with: what a successful result looks like, and the one thing to check if it fails.
- Prefer built-in Windows/PowerShell commands and the user's own `sysdiag` tool. Do NOT invent
  commands, flags, or file paths. If you're unsure a command exists or is safe, say so instead of
  guessing.
- BEFORE any destructive or risky step (deleting files, editing the registry, killing processes,
  anything elevated), put a one-line warning so the user reads it before running.

Hard rules:
- You only ADVISE. You never run anything — the user runs the steps and decides.
- The FINDINGS list is deterministic ground truth from a rules engine. Trust it over your own
  inference; if you disagree with the findings, the findings win.
- Use the STATIC FACTS to judge what's normal for THIS machine and where things live.
- Ground every recommendation in the live snapshot + findings below; cite the actual numbers.
  If the data doesn't show something, say so. Never invent readings, events, or commands.

{ctx}"""

def _text(content):
    """Ollama's /api/chat needs content as a plain string; Gradio sometimes hands a
    list of parts (e.g. [{'type':'text','text':...}]) which Ollama 400s on."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return "" if content is None else str(content)


def ask(message, history):
    """Gradio ChatInterface fn (type='messages'): history is [{role,content}, ...]."""
    user_text = _text(message)
    msgs = [{"role": "system", "content": SYSTEM.format(ctx=context.build(user_text))}]
    msgs += [{"role": m["role"], "content": _text(m.get("content"))} for m in (history or [])]
    msgs.append({"role": "user", "content": user_text})
    body = json.dumps({"model": MODEL, "messages": msgs, "stream": False,
                       "keep_alive": "30m",  # stay resident between messages; reload only after long idle
                       "options": {"temperature": 0.3, "num_ctx": 32768}}).encode()
    req = urllib.request.Request(OLLAMA, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:  # 300s survives a 19GB cold load
            return json.loads(r.read())["message"]["content"]
    except urllib.error.HTTPError as e:  # show Ollama's own error, not a generic "can't reach"
        return f"(Ollama returned HTTP {e.code}: {e.read().decode(errors='replace')[:300]})"
    except Exception as e:
        return f"(couldn't reach Ollama at {OLLAMA}: {e}. Is `ollama` running? Try `ollama ps`.)"


def demo():  # the one runnable check: a grounded answer comes back (needs Ollama up)
    # the bug this guards: list-shaped content must flatten to a string, not 400 Ollama
    assert _text([{"type": "text", "text": "a"}, {"text": "b"}]) == "ab"
    assert _text("hi") == "hi" and _text(None) == ""
    reply = ask("Is anything wrong right now? One sentence.", [])
    assert isinstance(reply, str) and reply.strip(), "no reply from the brain"
    print("brain ok:", reply[:160])


if __name__ == "__main__":
    demo()
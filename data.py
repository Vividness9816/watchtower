import sys, random
import schema, rules
from schema import EOS

DOC_TMPL = "INPUT\n{metrics}\nREPORT\n{report}" + EOS

_OPEN = {
    "OK":       ["All systems nominal.", "Everything looks healthy.", "Hardware is running clean."],
    "WARNING":  ["Heads up - something needs attention.", "One subsystem is running warm."],
    "CRITICAL": ["Critical condition detected.", "Something is in the red."],
}


def render_report(snap, findings, rng) -> str:
    st = "CRITICAL" if any(f["level"] == "CRIT" for f in findings) else "WARNING" if findings else "OK"
    lines = [f"{st}: {rng.choice(_OPEN[st])}", schema.summarize(snap)]
    for f in findings:
        verb = "is critical at" if f["level"] == "CRIT" else "is elevated at"
        if isinstance(f["limit"], (int, float)):
            lines.append(f"{f['what']} {verb} {f['value']}{f['unit']} (limit {f['limit']}{f['unit']}).")
        else:
            lines.append(f"{f['what']}: {f['value']}.")
    if st == "OK":
        lines.append(rng.choice(["No action needed.", "Continue normal operation."]))
    return " ".join(lines)


def build_corpus(n_docs: int, seed: int = 1337) -> str:
    rng = random.Random(seed)
    docs = []
    for _ in range(n_docs):
        snap = schema.synthetic_snapshot(rng)
        docs.append(DOC_TMPL.format(metrics=schema.serialize_metrics(snap),
                                    report=render_report(snap, rules.diagnose(snap), rng)))
    return "".join(docs)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    text = build_corpus(n)
    with open("corpus.txt", "w", encoding="utf-8") as f:
        f.write(text)
    n_alert = text.count("CRITICAL:") + text.count("WARNING:")
    print(f"wrote corpus.txt: {n} docs, {len(text):,} chars, "
          f"{len(set(text))} unique chars, ~{n_alert} with alerts")
    print("--- sample document ---")
    print(text.split(EOS)[0])


if __name__ == "__main__":
    main()
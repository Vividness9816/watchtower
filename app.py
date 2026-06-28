"""app.py — Watch Tower: live stats, chat, and history graphs. READ-ONLY, 127.0.0.1 only."""
import gradio as gr
import schema, brain, context, art, trends


def stats_md() -> str:
    snap, findings = context.snapshot_and_findings()
    head = schema.summarize(snap)
    lines = [f"### Live\n{head}", "", "### Findings"]
    if findings:
        order = {"CRIT": 0, "WARN": 1}
        for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
            lines.append(f"- **[{f['level']}]** {f['what']}: {f['value']}{f['unit']}")
    else:
        lines.append("- OK — no findings")
    d = snap.get("docker", {})
    if d and "error" not in d:
        lines.append(f"\n**Docker:** {d.get('running')}/{d.get('total')} running")
    if "_note" in snap:
        lines.append(f"\n> {snap['_note']}")
    return "\n".join(lines)


def plot(metric, rng):
    return trends.series(metric, rng)


with gr.Blocks(title="Watch Tower") as app:
    gr.HTML(art.html_banner())
    gr.Markdown("# Watch Tower — your system, explained")
    with gr.Row():
        with gr.Column(scale=1):
            panel = gr.Markdown(stats_md())
            gr.Timer(5).tick(stats_md, outputs=panel)
        with gr.Column(scale=2):
            gr.ChatInterface(
                fn=brain.ask,
                title="Ask about this machine",
                examples=["Is anything overheating?",
                          "What's eating my disk space?",
                          "Are there any hardware errors?",
                          "Is my GPU temp normal for this card?"],
            )
    gr.Markdown("## History")
    with gr.Row():
        metric = gr.Dropdown(list(trends.METRICS), value="CPU temp (C)", label="Component / metric")
        runs = gr.Dropdown(list(trends.RUNS), value="Last 25 runs", label="Show")
    graph = gr.LinePlot(trends.series("CPU temp (C)", "Last 25 runs"),
                        x="time", y="value", tooltip=["when", "value"],
                        title="History", height=320)
    metric.change(plot, [metric, runs], graph)
    runs.change(plot, [metric, runs], graph)


if __name__ == "__main__":
    art.cli_banner()
    try:
        app.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
    finally:
        import subprocess  # free the model's VRAM on clean exit (Ctrl+C / window close)
        subprocess.run(["ollama", "stop", brain.MODEL], check=False)
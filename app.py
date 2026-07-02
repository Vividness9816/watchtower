"""app.py — Watch Tower: live stats, chat, and history graphs. READ-ONLY, 127.0.0.1 only."""
import gradio as gr
import schema, brain, context, art, trends, live

if gr.NO_RELOAD:   # guard: `gradio app.py` reload mode re-imports modules — without this,
    #              every source edit would leak one more immortal sampler thread.
    if live.REMOTE:
        live.start_receiver()   # monitoring another machine: data arrives via ship.py/NiFi
    else:
        live.start()            # monitoring THIS machine: local two-tier sampler
#                Background sampler: fast metrics every 5s, full fleet every 60s. The stats
#                panel, live graphs AND the chat brain all read its cache — nothing in the
#                UI spawns the collector fleet per tick anymore.


WAITING = "(waiting for data)"


def refresh_hosts(current):
    """Keep the host selector's choices current and point the chat at the visible host.
    In local mode this is a single host; in remote mode new agents appear here live."""
    hs = live.hosts()
    if not hs:
        return gr.update(choices=[WAITING], value=WAITING)
    val = current if current in hs else hs[0]
    live.set_focus(val)                     # the chat brain answers about the selected host
    return gr.update(choices=hs, value=val)


def stats_md(host) -> str:
    live.set_focus(host)                    # default for the host=None fallback path (CLI chat)
    snap, findings = context.snapshot_and_findings(host)   # explicit host: no cross-tab clobber
    head = schema.summarize(snap)
    ident = snap.get("_host", host)
    label = snap.get("_label")
    age = snap.get("_snapshot_age_s")
    fresh = f" *(sampled {age}s ago)*" if age is not None else ""
    title = f"### {ident}" + (f" — {label}" if label else "") + fresh
    lines = [f"{title}\n{head}", "", "### Findings"]
    if findings:
        order = {"CRIT": 0, "WARN": 1}
        for f in sorted(findings, key=lambda x: order.get(x["level"], 9)):
            lines.append(f"- **[{f['level']}]** {f['what']}: {f['value']}{f['unit']}")
    else:
        lines.append("- OK — no findings")
    d = snap.get("docker", {})
    if d and "error" not in d:
        lines.append(f"\n**Docker:** {d.get('running')}/{d.get('total')} running")
    tags = snap.get("_tags")
    if isinstance(tags, dict) and tags:
        lines.append("\n" + " · ".join(f"`{k}={v}`" for k, v in tags.items()))
    if "_note" in snap:
        lines.append(f"\n> {snap['_note']}")
    return "\n".join(lines)


def plot(metric, rng):
    return trends.series(metric, rng)


_init_hosts = live.hosts()
_init_host = _init_hosts[0] if _init_hosts else WAITING


def live_plot_component(sel, span, host):
    # return a FULL component, not a bare DataFrame: the plot frontend freezes its
    # series/color encoding from the first value it receives, so bare-value updates
    # silently drop any series that wasn't present at page load (e.g. everything,
    # when the page loads seconds after app start). Rebuilding the component each
    # tick re-derives the encoding, so new series appear live.
    return gr.LinePlot(live.frame(sel, span, host=host), x="time", y="value", color="series",
                       title="Live (5s fast tier; net/whea/vm/services every 60s)", height=320)


DEFAULT_SEL = ["CPU temp (C)", "GPU temp (C)", "Liquid temp (C)"]

with gr.Blocks(title="Watch Tower") as app:
    gr.HTML(art.html_banner())
    gr.Markdown("# Watch Tower — your system, explained")
    host_sel = gr.Dropdown(_init_hosts or [WAITING], value=_init_host, label="Host",
                           info="which monitored machine to view (local mode: just this one)")
    with gr.Row():
        with gr.Column(scale=1):
            panel = gr.Markdown(stats_md(_init_host))
            gr.Timer(5).tick(refresh_hosts, inputs=host_sel, outputs=host_sel)
            gr.Timer(5).tick(stats_md, inputs=host_sel, outputs=panel)
        with gr.Column(scale=2):
            gr.ChatInterface(
                fn=brain.ask,
                additional_inputs=[host_sel],   # the selected host reaches brain.ask -> context,
                #                                 so the chat answers about the host you're viewing
                title="Ask about the selected host",
                # list-of-lists (message + each additional input) is required once
                # additional_inputs is set; host is left to default per example
                examples=[["Is anything overheating?"],
                          ["What's eating my disk space?"],
                          ["Are there any hardware errors?"],
                          ["Any failed services or stopped VMs?"]],
            )
    gr.Markdown("## Live graphs")
    with gr.Row():
        live_sel = gr.Dropdown(list(live.METRICS), multiselect=True, label="Metrics",
                               value=DEFAULT_SEL)
        live_span = gr.Dropdown(list(live.SPANS), value="15 min", label="Window")
    live_plot = live_plot_component(DEFAULT_SEL, "15 min", _init_host)
    gr.Timer(5).tick(live_plot_component, inputs=[live_sel, live_span, host_sel], outputs=live_plot)
    live_sel.change(live_plot_component, [live_sel, live_span, host_sel], live_plot)
    live_span.change(live_plot_component, [live_sel, live_span, host_sel], live_plot)
    host_sel.change(stats_md, host_sel, panel)
    host_sel.change(live_plot_component, [live_sel, live_span, host_sel], live_plot)

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
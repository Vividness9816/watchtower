# test_security.py — regression guard for the hardening pass (red-team RED-001..004).
# Assert-based, no framework, matches the repo's self-test style: `python test_security.py`.
import os, re, sys, tempfile, pathlib

os.environ["WATCHTOWER_NOTES_DB"] = str(pathlib.Path(tempfile.mkdtemp()) / "n.db")
import notes, live, search, app  # noqa: E402

# a real stored-XSS is a parseable HTML tag-open surviving into the rendered markdown; "onerror="
# as escaped TEXT (its <> turned to entities) is inert and does not count.
_TAG_OPEN = re.compile(r"<\s*/?[a-zA-Z]")
_XSS = ['<img src=x onerror=alert(1)>', '[click](javascript:alert(1))', '<script>alert(1)</script>',
        '</td><svg onload=alert(1)>']


def test_notes_xss_escaped():
    for p in _XSS:
        notes.add_note("attacker", p)
    r = app.render_notes()
    assert not _TAG_OPEN.search(r), "a raw HTML tag-open survived note rendering (stored XSS)"
    assert "](javascript:" not in r, "a javascript: markdown link survived"
    assert "&lt;" in r, "escaping did not run"


def test_remote_panel_xss_escaped():
    live._hosts.clear()
    live._record({"cpu": {"load": 10}, "sensors": {"cpu_temp": 40},
                  "_note": "<img src=x onerror=alert(2)>", "_label": "<script>bad</script>",
                  "_tags": {"k": "<svg onload=alert(3)>"}}, merge=False, host="evil")
    md = app.stats_md("evil")
    assert not _TAG_OPEN.search(md), "a raw HTML tag-open survived the remote panel (stored XSS)"
    assert "&lt;" in md, "panel escaping did not run"


def test_search_component_cap():
    r = search.search(component="x" * 100000)      # must not hang; component is capped internally
    assert isinstance(r, list)


def test_host_cardinality_cap():
    live._hosts.clear()
    for i in range(live.MAX_HOSTS):
        live._record({"cpu": {"load": 1}}, merge=False, host=f"h{i}")
    live._record({"cpu": {"load": 1}}, merge=False, host="one-too-many")
    assert len(live._hosts) == live.MAX_HOSTS and "one-too-many" not in live._hosts, "host cap not enforced"


if __name__ == "__main__":
    for fn in (test_notes_xss_escaped, test_remote_panel_xss_escaped,
               test_search_component_cap, test_host_cardinality_cap):
        fn()
        print(f"  ok  {fn.__name__}")
    print("security ok")

"""Build index.html for the Episode Dashboard Redesign artifact page.

The builder embeds files; it never draws (artifact guide §2.7). It reads page_template.html and
substitutes every {{TOKEN}}:
    {{FONT:Regular|SemiBold}}   Pretendard subset (assets/fonts/pretendard/subset), base64
    {{FIG:<stem>}}              figures/<stem>.png as a data URI
    {{DIM:<stem>}}              "W x H" of that PNG, read from the file
    {{SAMPLES:<stem>}}          used/available/percentage table, from figures/<stem>.data.txt or, for the
                                renderer-output figures, figures/frames_meta.json (both emitted by scripts)
    {{FRAMES:fig03_frames}}     JSON list of the per-step PNGs as data URIs (the step scrubber)
    {{DATA:episode}}            data/episode.json (numbers table beside the scrubber)
    {{FACT:<name>}}             numbers computed from data/episode.json
    {{REVIEW}}                  review.html next to this file (plan-review status)

Refuses to write the page (non-zero exit) when:
    - any token is unresolved or any input file is missing;
    - a <figure> draws in the page (inline <svg> or <canvas>) (§2.7);
    - a house-style figure (fig03_*, fig04_*) lacks its generating script or any of png/svg/pdf/data.txt (§2.7);
    - the scrubber frame count differs from the episode's step count;
    - a <figure> lacks an <b>Axes.</b> sentence, a data-used table, or a 150-250 word
      "How it is computed" block (§11);
    - the visible text uses "pain" as a description (vocabulary rule; the repo name is allowed);
    - the page script fails to parse (§3.2; esprima).

Run from anywhere:
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python docs/develop/active/refactors/renderer_layout_redesign/build_page.py
"""
import base64
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
FIGS = os.path.join(HERE, "figures")
FONTS = os.path.join(ROOT, "assets", "fonts", "pretendard", "subset")
SCRIPT_OF = {"fig03_proposed_dashboard": "fig03_proposed_dashboard.py", "fig04_repacking": "fig03_proposed_dashboard.py",
             "v1_thermal": "render_current_frames.py", "v2_thermal": "render_current_frames.py"}
errors = []


def read(path, mode="r"):
    if not os.path.exists(path):
        errors.append(f"missing input: {os.path.relpath(path, ROOT)}")
        return b"" if "b" in mode else ""
    with open(path, mode) as fh:
        return fh.read()


def b64png(path):
    return "data:image/png;base64," + base64.b64encode(read(path, "rb")).decode()


def samples_table(rows, label):
    if not rows:
        errors.append(f"no data-used statement for {label}")
        return ""
    body = []
    for r in rows:
        used, total = int(r["used"]), int(r["total"])
        pct = 100.0 * used / total if total else 0.0
        body.append(f"<tr><td>{html.escape(r['what'])}</td><td class=\"n\">{used}</td><td class=\"n\">{total}</td>"
                    f"<td class=\"n\">{pct:.0f}%</td><td>{html.escape(r['note'])}</td></tr>")
    # no `wide` floor: that floor is sized for the toolkit table and hid this table's last column inside
    # a half-width figure column (format review 2026-09-14, register F34)
    return ("<p class=\"cue\" hidden>&larr; wider than the column &mdash; scroll sideways; the right-hand column is cut off</p>"
            "<div class=\"scroll\"><table class=\"samples\"><thead><tr><th>Data used</th><th class=\"n\">used</th>"
            "<th class=\"n\">available</th><th class=\"n\">share</th><th>why</th></tr></thead><tbody>"
            + "".join(body) + "</tbody></table></div>")


def samples(stem):
    txt = os.path.join(FIGS, f"{stem}.data.txt")
    if os.path.exists(txt):
        rows = []
        for line in read(txt).splitlines():
            what, used, total, note = line.split("\t")
            rows.append(dict(what=what, used=used, total=total, note=note))
        return samples_table(rows, stem)
    return samples_table(frames_meta.get(stem, {}).get("samples"), stem)


page = read(os.path.join(HERE, "page_template.html"))
frames_meta = json.loads(read(os.path.join(FIGS, "frames_meta.json")) or "{}")
episode_raw = read(os.path.join(HERE, "data", "episode.json"))
episode = json.loads(episode_raw or '{"meta":{},"steps":[]}')
review = read(os.path.join(HERE, "review.html"))
meta, steps = episode["meta"], episode["steps"]
REP_STEP = 15   # the still shown before the scrubber loads; matches fig03_proposed_dashboard.py


def fact(name):
    if name == "final_temp":
        return f"{steps[-1]['body_temp']:+.1f}".replace("-", "−")
    if name == "last_step":
        return str(len(steps) - 1)
    if name == "rep_step":
        return str(REP_STEP)
    if name == "die_low":
        return f"{meta['min_temperature']:+.0f}".replace("-", "−")
    if name == "clim":
        return f"{meta['clim'][0]:+.0f} to {meta['clim'][1]:+.0f}".replace("-", "−")
    errors.append(f"unknown fact {name}")
    return ""


def frames(stem):
    d = os.path.join(FIGS, stem)
    files = sorted(f for f in os.listdir(d) if f.endswith(".png")) if os.path.isdir(d) else []
    if len(files) != len(steps):
        errors.append(f"{stem}: {len(files)} frames on disk but the episode has {len(steps)} steps -- rerun fig03_proposed_dashboard.py")
    return json.dumps([b64png(os.path.join(d, f)) for f in files])


def substitute(m):
    kind, _, arg = m.group(1).partition(":")
    if kind == "FONT":
        return base64.b64encode(read(os.path.join(FONTS, f"Pretendard-{arg}.latin.woff"), "rb")).decode()
    if kind == "FIG":
        script = SCRIPT_OF.get(arg)
        if not script or not os.path.exists(os.path.join(HERE, script)):
            errors.append(f"{arg}: shown on the page but no generating script")
        if arg.startswith(("fig03", "fig04")):
            for ext in ("svg", "pdf", "data.txt"):
                if not os.path.exists(os.path.join(FIGS, f"{arg}.{ext}")):
                    errors.append(f"{arg}: no {ext} -- run {script}")
        return b64png(os.path.join(FIGS, f"{arg}.png"))
    if kind == "DIM":
        data = read(os.path.join(FIGS, f"{arg}.png"), "rb")
        return f"{int.from_bytes(data[16:20], 'big')} &times; {int.from_bytes(data[20:24], 'big')}"
    if kind == "SAMPLES":
        return samples(arg)
    if kind == "FRAMES":
        return frames(arg).replace("</", "<\\/")
    if kind == "DATA":
        if arg != "episode":
            errors.append(f"unknown data blob {arg}")
            return ""
        return episode_raw.replace("</", "<\\/")
    if kind == "FACT":
        return fact(arg)
    if kind == "REVIEW":
        return review
    errors.append(f"unknown token {m.group(0)}")
    return ""


page = re.sub(r"\{\{([A-Z]+(?::[A-Za-z0-9_]+)?)\}\}", substitute, page)
if re.search(r"\{\{[A-Z]+(?::[A-Za-z0-9_]+)?\}\}", page):
    errors.append("unresolved tokens remain")

# per-figure checks, one <figure> at a time (never a regex spanning figures -- guide §11 trap)
for i, fig in enumerate(re.findall(r"<figure\b.*?</figure>", page, flags=re.S), 1):
    if re.search(r"<(svg|canvas)\b", fig):
        errors.append(f"figure {i}: draws in the page (inline <svg>/<canvas>) -- figures come from scripts (§2.7)")
    cap = re.search(r"<figcaption>(.*?)</figcaption>", fig, flags=re.S)
    cap = cap.group(1) if cap else ""
    if "<b>Axes.</b>" not in cap:
        errors.append(f"figure {i}: no <b>Axes.</b> sentence")
    if "table class=\"samples" not in cap:
        errors.append(f"figure {i}: no data-used table")
    how = re.search(r'How it is computed</p>\s*<p>(.*?)</p>', cap, flags=re.S)
    if not how:
        errors.append(f"figure {i}: no 'How it is computed' block")
    else:
        n = len(re.sub(r"<[^>]+>", " ", how.group(1)).split())
        if not 150 <= n <= 250:
            errors.append(f"figure {i}: 'How it is computed' is {n} words (want 150-250)")

visible = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<[^>]+>", " ", page, flags=re.S)
for hit in re.finditer(r"[A-Za-z_]*pain[A-Za-z_]*", visible, flags=re.I):
    if hit.group(0).lower() != "grid_world_pain":
        errors.append(f"vocabulary: '{hit.group(0)}' in visible text (say nociception)")

try:
    import esprima
    for s in re.findall(r"<script>(.*?)</script>", page, flags=re.S):
        esprima.parseScript(s)
except ImportError:
    errors.append("cannot check the page script: esprima is not installed")
except Exception as exc:  # esprima parse error
    errors.append(f"page script does not parse: {exc}")

if errors:
    print("BUILD FAILED -- index.html not written:")
    for e in errors:
        print("  -", e)
    sys.exit(1)

out = os.path.join(HERE, "index.html")
with open(out, "w") as fh:
    fh.write(page)
print(f"wrote {os.path.relpath(out, ROOT)} ({len(page) / 1e6:.2f} MB), {len(steps)} steps, seed {meta['seed']}")

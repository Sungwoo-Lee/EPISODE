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

Figures 3 and 4 are the RENDERER'S OWN raster output, written by render_examples.py from a real
recording, and are therefore checked like Figures 1-2 (png + a data-used statement) rather than like a
house-style figure: they carry no svg/pdf, because a vector redraw of a video frame would be a picture
of something other than what the renderer produces. Figures 5-8 ARE drawn in the house style and must
carry the full png/svg/pdf/data.txt set.
    {{REVIEW}}                  review.html next to this file (plan-review status)

Refuses to write the page (non-zero exit) when:
    - any token is unresolved or any input file is missing;
    - a <figure> draws in the page (inline <svg> or <canvas>) (§2.7);
    - a figure lacks its generating script, its png or its data.txt, or a house-style figure
      (fig05_* .. fig08_*) lacks its svg or pdf (§2.7);
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
SCRIPT_OF = {"fig03_rendered_dashboard": "render_examples.py", "fig04_three_worlds": "render_examples.py",
             "fig05_option_a_channel_maps": "fig05_extended_encodings.py",
             "fig06_option_b_dominant_channel": "fig05_extended_encodings.py",
             "fig07_option_c_bars_or_table": "fig05_extended_encodings.py",
             "fig08_icon_set": "fig08_icon_set.py",
             "fig09_range1_maps": "render_examples.py",
             "v1_thermal": "render_current_frames.py", "v2_thermal": "render_current_frames.py"}
#: The figures drawn in the house style, which must carry vector siblings. Figures 3-4 are the
#: renderer's own PNG output and are deliberately not in this set (see the module docstring).
HOUSE_STYLE = ("fig05", "fig06", "fig07", "fig08")
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
        body.append(f"<tr class=\"num\"><td>{html.escape(r['what'])}</td><td class=\"n\">{used}</td><td class=\"n\">{total}</td>"
                    f"<td class=\"n\">{pct:.0f}%</td></tr>"
                    f"<tr class=\"why\"><td colspan=\"4\">{html.escape(r['note'])}</td></tr>")
    # The reason sits on its own full-width row under its numbers. Two prose columns beside three numeric
    # ones squeezed one or the other into a ribbon at every narrow width (layout checker, 2026-09-14).
    return ("<p class=\"cue\" hidden>&larr; wider than the column &mdash; scroll sideways; the right-hand column is cut off</p>"
            "<div class=\"scroll\"><table class=\"samples\"><thead><tr><th>Data used</th><th class=\"n\">used</th>"
            "<th class=\"n\">available</th><th class=\"n\">share</th></tr></thead><tbody>"
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
# The still shown before the scrubber loads. READ from the export rather than repeated here: the
# renderer picks the step, writes the PNG for it and records it in meta, so this cannot drift out of
# step with the image on the page the way a second copy of the number could.
REP_STEP = int(meta.get("rep_step", 0))


def fact(name):
    if name == "final_temp":
        return f"{steps[-1]['body_temp']:+.1f}".replace("-", "−")
    if name in ("final_nutrition", "final_satiation"):
        field = name.split("_")[1]
        return f"{steps[-1][field] / meta['max_' + field]:.2f}"
    if name == "coldest_body":
        return f"{min(s['body_temp'] for s in steps):+.1f}".replace("-", "−")
    if name == "shared_steps":
        return str(sum(1 for s in steps if s.get("shared")))
    # last_step / rep_step are the EPISODE'S OWN step numbers, for prose. last_index /
    # rep_index are positions in the frame list, for the slider. They diverge as soon as the
    # scrubber subsamples (meta.frame_stride), and confusing the two would caption a 74-step
    # episode as ending at step 37.
    if name == "last_step":
        return str(steps[-1]["t"])
    if name == "last_index":
        return str(len(steps) - 1)
    if name == "rep_step":
        return str(REP_STEP)
    if name == "rep_index":
        return str(int(meta.get("rep_index", 0)))
    if name == "die_low":
        return f"{meta['min_temperature']:+.0f}".replace("-", "−")
    if name in ("temp_min", "temp_max"):
        field = [v for row in meta["thermal_field"] for v in row]
        v = min(field) if name == "temp_min" else max(field)
        return f"{v:+.1f}".replace("-", "\u2212")
    if name == "clim":
        return f"{meta['clim'][0]:+.0f} to {meta['clim'][1]:+.0f}".replace("-", "−")
    errors.append(f"unknown fact {name}")
    return ""


def frames(stem):
    d = os.path.join(FIGS, stem)
    files = sorted(f for f in os.listdir(d) if f.endswith(".png")) if os.path.isdir(d) else []
    if len(files) != len(steps):
        errors.append(f"{stem}: {len(files)} frames on disk but data/episode.json lists {len(steps)} drawn steps -- rerun render_examples.py")
    return json.dumps([b64png(os.path.join(d, f)) for f in files])


def substitute(m):
    kind, _, arg = m.group(1).partition(":")
    if kind == "FONT":
        return base64.b64encode(read(os.path.join(FONTS, f"Pretendard-{arg}.latin.woff"), "rb")).decode()
    if kind == "FIG":
        script = SCRIPT_OF.get(arg)
        if not script or not os.path.exists(os.path.join(HERE, script)):
            errors.append(f"{arg}: shown on the page but no generating script")
        if arg.startswith("fig"):
            exts = ("data.txt",) + (("svg", "pdf") if arg.startswith(HOUSE_STYLE) else ())
            for ext in exts:
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

# every generating script is named on the page, so a reader can regenerate every figure (register F15 family)
for script in sorted(set(SCRIPT_OF.values()) | {"export_extended.py", "make_dashboard_assets.py", "dashboard_style.py", "build_page.py"}):
    if script not in visible:
        errors.append(f"generating script {script} is not named anywhere on the page (add it to the Regenerate paragraph)")
# whole words only: "paints" is not the explanandum, and the repository name is allowed
for hit in re.finditer(r"(?<![A-Za-z])[A-Za-z_]*pain(?:s|ful|less)?(?![A-Za-z])", visible, flags=re.I):
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

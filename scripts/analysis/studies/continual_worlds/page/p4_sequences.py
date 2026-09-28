"""FIGURE p4 — The run plan as a timeline: which world each run trains in, over the episode counter.

Everything is read, never typed:
  * main sequences P1-P3: every non-pilot schedule YAML in configs/continual/continual_worlds/ (its
    `continual.episode_boundaries`) plus its `<name>_stages/` folder, whose stage files name their
    concept world through `extends:`. A stage starts where the previous boundary ends; stage 1 starts one
    stage-length before the first boundary (the restored pre-training counter, ~10 M).
  * Pilot 2 (short A-B-A-B): a schedule YAML with 'pilot' in its name if one exists; otherwise the
    boundaries and the two sequences named in the design doc's plan-review (row F1 / "Pilot 2" text).
  * Pilot 1 (single switch from the pre-trained Home agent into each new concept): the concepts from the
    design doc's survivability-pilot section (3.6) and the `--episodes` budget of the manifest row for
    the pilot runs (section 4.1).
  * Pilot 3 (Nursery from scratch): the `--episodes` budget of the manifest's Nursery-leg row.
The pre-trained agents' Home stage (episodes 0-10 M, level-05 factorial) is the start of every run
except Pilot 3 and is not drawn as a block. Pilot 3 starts from an empty counter and is drawn in a
narrow left panel on its own scale.
"""
import glob, re, sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml, numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
import _common as C

house = C.house; house.apply()
doc = C.doc_text()
M = 1e6


def concept_of_stage(path):
    ext = yaml.safe_load(open(path))["extends"]
    stem = os.path.basename(ext)
    hit = [c for c in C.CONCEPTS if stem.startswith(c.lower() + "_")]
    assert len(hit) == 1, (path, ext)
    return hit[0]


def schedule(ypath):
    b = [int(x) for x in yaml.safe_load(open(ypath))["continual"]["episode_boundaries"]]
    sdir = ypath[:-5] + "_stages"
    stages = sorted(glob.glob(os.path.join(sdir, "*.yaml")))
    assert len(stages) == len(b), (ypath, len(stages), len(b))
    length = b[1] - b[0]
    starts = [b[0] - length] + b[:-1]
    return [(concept_of_stage(s), st, en) for s, st, en in zip(stages, starts, b)]


def seq_name(ypath):
    """'P1 Danger ↔ Famine' from p1_danger_famine.yaml"""
    tag = os.path.basename(ypath).split("_")[0].upper()
    return tag


# ---- main sequences ------------------------------------------------------------------------------
sched_files = sorted(glob.glob(os.path.join(C.SCHED_DIR, "*.yaml")))
main = {seq_name(f): schedule(f) for f in sched_files if "pilot" not in os.path.basename(f)}
pilot2_files = [f for f in sched_files if "pilot" in os.path.basename(f)]
assert main, "no main schedules found"
first = min(s[0][1] for s in main.values())            # the restored pre-training counter (10 M)

# ---- Pilot 2 -------------------------------------------------------------------------------------
pilot2, p2_source = {}, None
if pilot2_files:
    for i, f in enumerate(pilot2_files):
        pilot2[f"Pilot 2{'abcdefgh'[i]}"] = schedule(f)
    p2_source = "pilot schedule files"
else:
    m = re.search(r"Pilot 2 needs two new schedule files with boundaries `\[([0-9M, ]+)\]`", doc)
    pairs = re.search(r"\(Pilot 2\) short 1 M-per-stage A-B-A-B runs of (P\d) and (P\d)", doc)
    assert m and pairs, "Pilot 2 is neither in a schedule file nor in the design doc"
    b = [int(float(x.strip().rstrip("M")) * M) for x in m.group(1).split(",")]
    for i, tag in enumerate(pairs.groups()):
        src = main[tag]
        assert len(src) == len(b), (tag, len(src), b)
        L = b[1] - b[0]
        pilot2[f"Pilot 2{'ab'[i]} ({tag}'s worlds)"] = [(c, st, en) for (c, _, _), st, en in zip(src, [b[0] - L] + b[:-1], b)]
    p2_source = "design doc plan-review row F1 (no pilot schedule file yet)"

# ---- Pilot 1 and Pilot 3 from the design doc -----------------------------------------------------
sec = re.search(r"One pilot per new concept \(([^)]+)\)", doc)
assert sec, "design doc section 3.6 pilot list not found"
p1_concepts = [c.strip() for c in sec.group(1).split(",")]
row = re.search(r"^\| 1–6 \|.*?--episodes (\d+)", doc, re.M)
assert row, "manifest row for the pilot runs (1–6) not found"
p1_end = int(row.group(1))
nur = re.search(r"^\| 13–16 \| `(\w+)\.yaml`.*?--episodes (\d+)", doc, re.M)
assert nur, "manifest row for the Nursery legs (13–16) not found"
nur_concept = [c for c in C.CONCEPTS if nur.group(1).startswith(c.lower() + "_")][0]
p3_end = int(nur.group(2))

# ---- rows, top to bottom -------------------------------------------------------------------------
rows = [(f"Pilot 1 · {c}", [(c, first, p1_end)]) for c in p1_concepts]
rows += list(pilot2.items())
rows += [("Pilot 3 · from scratch", "left")]
rows += [(f"{k} (main)", v) for k, v in main.items()]
STYLE = {"Nursery": dict(fc="white", hatch="...."), "Home": dict(fc="#eceeeb"),
         "Forage": dict(fc="#dfe2de"), "Danger": dict(fc="#a3a8a3"),
         "Famine": dict(fc="white", hatch="////"), "Winter": dict(fc="#c9cdc8", hatch="\\\\\\\\"),
         "Fog": dict(fc="white", hatch="xx"), "Harsh": dict(fc="#80867f")}
last = max(max(en for _, _, en in v) for _, v in rows if v != "left")

fig = plt.figure(figsize=(9.9, 6.2))
axL = fig.add_axes([0.155, 0.17, 0.10, 0.76]); axR = fig.add_axes([0.285, 0.17, 0.70, 0.76], sharey=axL)
n = len(rows)


def block(ax, c, st, en, y, ret):
    s = STYLE[c]
    ax.add_patch(Rectangle((st / M, y - 0.36), (en - st) / M, 0.72, ec=house.INK_2, lw=0.8, **s))
    ax.text((st + en) / 2 / M, y, c, ha="center", va="center", fontsize=C.SMALLEST_PT, color=house.INK,
            bbox=dict(fc="white", ec="none", pad=1.6) if s.get("hatch") else None)
    if ret:
        ax.plot([st / M + 0.03, en / M - 0.03], [y - 0.44, y - 0.44], color=C.ACCENT, lw=2.6, solid_capstyle="butt")


n_blocks = n_ret = 0
for i, (lab, spec) in enumerate(rows):
    y = n - 1 - i
    if spec == "left":
        block(axL, nur_concept, 0, p3_end, y, False); n_blocks += 1
        continue
    seen = set()
    for c, st, en in spec:
        ret = c in seen and len(spec) > 2
        block(axR, c, st, en, y, ret); seen.add(c); n_blocks += 1; n_ret += ret
axL.set_yticks(range(n)); axL.set_yticklabels([r[0] for r in rows][::-1], fontsize=C.SMALLEST_PT, color=house.INK)
axL.set_ylim(-0.8, n - 0.4)
axL.set_xlim(0, p3_end / M * 1.05); axL.set_xticks([0, p3_end / M])
axL.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
axR.set_xlim(first / M - 0.2, last / M + 0.2)
axR.set_xticks(np.arange(first / M, last / M + 0.1, 1)); axR.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
plt.setp(axR.get_yticklabels(), visible=False)
for a in (axL, axR):
    a.tick_params(axis="y", length=0); a.grid(axis="y", visible=False); a.grid(axis="x", visible=True)
    for s in ("top", "right", "left"):
        a.spines[s].set_visible(False)
axR.axvline(first / M, color=house.INK_2, lw=1.0, ls=(0, (3, 2)))
fig.text(0.205, 0.075, "episodes from\nscratch (millions)", ha="center", va="center", fontsize=C.SMALLEST_PT, color=house.INK)
fig.text(0.635, 0.075, "episode counter (millions); dashed line: the pre-trained Home agents' counter", ha="center",
         va="center", fontsize=C.SMALLEST_PT, color=house.INK)
used = sorted({c for _, v in rows if v != "left" for c, _, _ in v} | {nur_concept}, key=C.CONCEPTS.index)
h = [Patch(ec=house.INK_2, lw=0.8, label=c, **STYLE[c]) for c in used]
h.append(Line2D([], [], color=C.ACCENT, lw=2.6, label="second visit (return)"))
fig.legend(handles=h, loc="lower center", ncol=len(h), frameon=False, fontsize=C.SMALLEST_PT, bbox_to_anchor=(0.57, 0.0),
           handlelength=1.6, columnspacing=1.0)
C.assert_ticks_dont_collide(axR, "x")

C.record_kind("p4_sequences", "design")
rec = [dict(what="main sequences read from schedule files", used=len(main), total=len(main),
            note="configs/continual/continual_worlds/*.yaml boundaries + their stage folders' extends: targets"),
       dict(what="Pilot 2 sequences", used=len(pilot2), total=len(pilot2), note=f"source: {p2_source}"),
       dict(what="Pilot 1 single-switch runs (one per new concept)", used=len(p1_concepts), total=len(p1_concepts),
            note=f"concepts from design doc section 3.6; budget --episodes {p1_end:,} from the manifest row for the pilots"),
       dict(what="Pilot 3 from-scratch run length (episodes)", used=p3_end, total=p3_end,
            note=f"manifest row for the {nur_concept} legs; drawn on its own counter from 0"),
       dict(what="stage blocks drawn / of which second visits", used=n_ret, total=n_blocks,
            note="a second visit = a world already visited earlier in the same run")]
C.record_samples("p4_sequences", rec)
for lab, spec in rows:
    print("  ", lab, spec if spec == "left" else [(c, st / M, en / M) for c, st, en in spec])
C.save(fig, "p4_sequences", check_text=False)

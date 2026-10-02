"""FIGURE p4 — The run plan as a timeline, after the pilots: which world each run trains in, over the
episode counter.

Everything is read, never typed:
  * WHICH sequences are drawn, and their status, comes from the design doc's revised-sequence table
    (section 3.7.4: one row per sequence with a Status cell -- READY or DRAFT -- and the schedule file it
    uses). Each file's own header marker ("READY" / "DRAFT -- PENDING USER APPROVAL") must agree with the
    doc, or the script stops.
  * Schedule files that 3.7.4 says must not be launched (the original P1 / P2, which use dropped worlds)
    are excluded by the glob patterns named in that sentence; every other non-pilot schedule file must be
    in the table, so a new file cannot silently vanish from the figure.
  * The Pilot 2 pipeline-check runs (files with 'pilot' in the name) are drawn as what actually ran.
  * Stage worlds: each schedule's `<name>_stages/` folder, whose stage files name their world through
    `extends:`. Boundaries: `continual.episode_boundaries`.
  * Stage 1 (Forage) starts at the pre-trained agents' restored episode counter, read from the pilot
    read-out's seed-42 Home runs (their training budget).
The single-world pilots (Pilot 1, the softened re-pilots, the scouts, Pilot 3) are the next figure (p5).
"""
import glob, json, os, re, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml, numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
import _common as C

house = C.house; house.apply()
doc = C.doc_text()
M = 1e6
RO = json.load(open(C.READOUT))
budgets = {v["budget"] for k, v in RO["home"].items() if k.endswith("_s42")}
assert len(budgets) == 1, budgets
PRE = next(iter(budgets))                           # the pre-trained agents' counter (10 M)


def world_label(stem):
    """'danger_scout_a_15x15' -> 'Danger-A'; 'winter_15x15' -> 'Winter'."""
    base = re.sub(r"_\d+x\d+$", "", stem)
    m = re.match(r"([a-z]+)_scout_([a-z])$", base)
    return f"{m.group(1).capitalize()}-{m.group(2).upper()}" if m else base.capitalize()


def stage_world(path):
    return world_label(os.path.basename(yaml.safe_load(open(path))["extends"]).removesuffix(".yaml"))


def schedule(ypath):
    b = [int(x) for x in yaml.safe_load(open(ypath))["continual"]["episode_boundaries"]]
    stages = sorted(glob.glob(os.path.join(ypath[:-5] + "_stages", "*.yaml")))
    assert len(stages) == len(b), (ypath, len(stages), len(b))
    return [(stage_world(s), st, en) for s, st, en in zip(stages, [PRE] + b[:-1], b)]


def header_status(ypath):
    head = "".join(open(ypath).readlines()[:12])
    if "DRAFT -- PENDING USER APPROVAL" in head:
        return "DRAFT"
    if re.search(r"^# READY \(", head, re.M):
        return "READY"
    if "PILOT 2" in head:
        return "PILOT"
    return "OTHER"


# ---- the revised-sequence table of design doc 3.7.4 ------------------------------------------------
sec = doc[doc.index("#### 3.7.4"):doc.index("#### 3.7.5")]
table = []
for line in sec.splitlines():
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) < 4 or not c[0].startswith("**"):
        continue
    f = re.search(r"`(configs/continual/continual_worlds/[\w]+\.yaml)`", c[3])
    st = re.match(r"\*\*(READY|DRAFT)\b", c[2])
    if f and st:
        name = re.match(r"\*\*([^*]+)\*\*", c[0]).group(1)
        table.append((name, st.group(1), os.path.join(C.ROOT, f.group(1))))
assert table, "no sequence rows with a status and a schedule file in design doc 3.7.4"
dropped = re.search(r"The original P1 / P2 files \(([^)]+)\) are left untouched; they use the\s+dropped "
                    r"worlds and must not be launched", sec)
assert dropped, "3.7.4 no longer names the must-not-launch files; update this script"
excl = [g.strip("` ") for g in dropped.group(1).split(",")]
sched_files = sorted(glob.glob(os.path.join(C.SCHED_DIR, "*.yaml")))
listed = {p for _, _, p in table}
excluded = [f for f in sched_files if any(re.fullmatch(g.replace("*", ".*"), os.path.basename(f)) for g in excl)]
pilots = [f for f in sched_files if "pilot" in os.path.basename(f)]
orphan = [f for f in sched_files if f not in listed and f not in excluded and f not in pilots]
assert not orphan, f"schedule files neither in 3.7.4, excluded, nor pilots: {orphan}"
for name, st, p in table:
    assert header_status(p) == st, f"{p}: header says {header_status(p)}, design doc 3.7.4 says {st}"
for p in pilots:
    assert header_status(p) == "PILOT", p

STATUS_TEXT = {"READY": "ready to launch", "DRAFT": "draft: needs approval", "PILOT": "ran: pipeline check"}
rows = [(f"Pilot 2{os.path.basename(p)[6]}", "PILOT", schedule(p)) for p in pilots]
rows += [(name, st, schedule(p)) for name, st, p in sorted(table, key=lambda t: t[1] != "READY")]
branch = {sp[0][2] for _, _, sp in rows}
assert len(branch) == 1, f"runs do not share one branch point: {branch}"
B0 = branch.pop()

STYLE = {"Home": dict(fc="#eceeeb"), "Forage": dict(fc="#dfe2de"), "Danger": dict(fc="#a3a8a3"),
         "Danger-A": dict(fc="#c9cdc8", hatch=".."), "Famine": dict(fc="white", hatch="////"),
         "Winter": dict(fc="#c9cdc8", hatch="\\\\\\\\"), "Fog": dict(fc="white", hatch="xx"),
         "Fog-B": dict(fc="white", hatch="++")}
last = max(en for _, _, sp in rows for _, _, en in sp)

fig = plt.figure(figsize=(9.9, 4.3))
ax = fig.add_axes([0.16, 0.25, 0.60, 0.70])
n = len(rows)
n_blocks = n_ret = 0
for i, (lab, st, spec) in enumerate(rows):
    y = n - 1 - i
    seen = set()
    for c, s0, en in spec:
        ret = c in seen
        sty = STYLE[c]
        ax.add_patch(Rectangle((s0 / M, y - 0.34), (en - s0) / M, 0.68, ec=house.INK_2, lw=0.8, **sty))
        ax.text((s0 + en) / 2 / M, y, c, ha="center", va="center", fontsize=C.SMALLEST_PT, color=house.INK,
                bbox=dict(fc="white", ec="none", pad=1.4) if sty.get("hatch") else None)
        if ret:
            ax.plot([s0 / M + 0.03, en / M - 0.03], [y - 0.42, y - 0.42], color=C.ACCENT, lw=2.6,
                    solid_capstyle="butt")
        seen.add(c); n_blocks += 1; n_ret += ret
    ax.text(1.02, y, STATUS_TEXT[st], transform=ax.get_yaxis_transform(), ha="left", va="center",
            fontsize=C.SMALLEST_PT, color=house.INK, fontweight="bold" if st == "READY" else "normal")
ax.set_yticks(range(n)); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=C.SMALLEST_PT, color=house.INK)
ax.set_ylim(-0.7, n - 0.4)
ax.set_xlim(PRE / M - 0.1, last / M + 0.1)
ax.set_xticks(np.arange(PRE / M, last / M + 0.1, 1)); ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
ax.tick_params(axis="y", length=0); ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.axvline(B0 / M, color=house.INK_2, lw=1.0, ls=(0, (3, 2)))
ax.set_xlabel("episode counter (millions), continuing from the pre-trained agents; dashed line: branch point",
              fontsize=C.SMALLEST_PT)
used = [c for c in STYLE if any(c == w for _, _, sp in rows for w, _, _ in sp)]
h = [Patch(ec=house.INK_2, lw=0.8, label=c, **STYLE[c]) for c in used]
h.append(Line2D([], [], color=C.ACCENT, lw=2.6, label="second visit"))
fig.legend(handles=h, loc="lower center", ncol=len(h), frameon=False, fontsize=C.SMALLEST_PT,
           bbox_to_anchor=(0.5, 0.0), handlelength=1.5, columnspacing=0.9)
C.assert_ticks_dont_collide(ax, "x")

C.record_kind("p4_sequences", "design")
rec = [dict(what="sequences drawn from design doc 3.7.4", used=len(table), total=len(table),
            note="status (ready / draft) from the doc's table, cross-checked against each schedule file's header"),
       dict(what="schedule files left out (must not launch)", used=0, total=len(excluded),
            note="the original P1 and P2 files; they use worlds the pilots dropped (3.7.4)"),
       dict(what="Pilot 2 pipeline-check runs drawn", used=len(pilots), total=len(pilots),
            note="what actually ran; its stages are too short to count as evidence"),
       dict(what="stage blocks drawn / of which second visits", used=n_ret, total=n_blocks,
            note="a second visit = a world already visited earlier in the same run")]
C.record_samples("p4_sequences", rec)
for lab, st, spec in rows:
    print("  ", lab, st, [(c, s0 / M, en / M) for c, s0, en in spec])
C.save(fig, "p4_sequences", check_text=False)

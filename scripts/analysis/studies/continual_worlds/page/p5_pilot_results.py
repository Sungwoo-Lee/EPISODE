"""FIGURE p5 — What the pilots showed: every pilot world's settled survival for both agents, against the
line each agent had to clear.

Everything is read, never typed. Source: results/analysis/continual_worlds/pilot_readout.json, written by
scripts/analysis/studies/continual_worlds/pilot_readout.py from the runs' own WandB episode rows.

  * value   = `S_trailing200k`: mean survival steps per episode over the run's last 200,000 episodes.
  * line    = the pass line of the pre-registered rule that applies to that run:
              - a world pilot (pre-registered, softened, or scout): `survivable.survival_line` = half of the
                agent's own Home level (design doc 3.6);
              - Nursery from scratch (Pilot 3): the `p3_criteria.survival` threshold; the row's verdict is
                `p3_pass.pass` (all six skill rows + no collapse, 3.6), not survival alone;
              - Home leg after Nursery (seed 43): the competence gate of design doc 3.5 = <fraction> x the
                same agent type's seed-42 Home level. The fraction is read from the doc and the product is
                checked against the doc's printed gate values.
  * state   = final when the run has ended (`finished`); otherwise provisional (hollow marker).
The Pilot 2 runs (A-B-A-B pipeline checks) have no single-world survival value and are not drawn.
"""
import json, math, os, re, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _common as C

house = C.house; house.apply()
doc = C.doc_text()
RO = json.load(open(C.READOUT))
runs = RO["runs"]

# ---- which runs, in which group, under which label ---------------------------------------------
# Groups are defined by the TAG family the readout assigns; labels are derived from the tag.
GROUPS = [("Pre-registered worlds", "rppo_cw_pilot1_"),
          ("Softened once, re-piloted", "rppo_cw_pilot1s_"),
          ("Scouts (not pre-registered)", "rppo_cw_scout_"),
          ("Fresh agents, seed 43", None)]
PRETTY = {"danger_soft": "Danger, softened", "fog_soft": "Fog, softened", "harsh_soft": "Harsh, softened",
          "danger_scout_a": "Danger-A", "danger_scout_b": "Danger-B", "danger_scout_c": "Danger-C",
          "fog_scout_a": "Fog-A", "fog_scout_b": "Fog-B", "nursery": "Nursery (from scratch)",
          "home": "Home, after Nursery"}


def family(tag):
    t = re.sub(r"_t(1none|16quad)_s\d+(_r\d+)?$", "", tag)
    for _, pre in GROUPS[:3]:
        if t.startswith(pre):
            return pre, t[len(pre):]
    assert t in ("rppo_cw_nursery", "rppo_cw_home"), tag
    return None, t[len("rppo_cw_"):]


def label(w):
    return PRETTY.get(w, w.capitalize())


# ---- seed-43 Home competence gate (design doc 3.5) ---------------------------------------------
m = re.search(r"mean survival is \*\*≥ (\d+) % of the same agent type's seed-42 Home level\*\* "
              r"\(ordinary\s+≥ ([\d.]+), modulated ≥ ([\d.]+)\)", re.sub(r"\s+", " ", doc))
assert m, "design doc 3.5 competence gate not found"
GATE_FRAC = int(m.group(1)) / 100
seed42 = {("ordinary" if "t1none" in k else "modulated"): v["level_last10pct"]
          for k, v in RO["home"].items() if k.endswith("_s42")}
gate = {a: GATE_FRAC * v for a, v in seed42.items()}
for a, printed in (("ordinary", float(m.group(2))), ("modulated", float(m.group(3)))):
    assert abs(gate[a] - printed) < 0.05, (a, gate[a], printed)


def point(r):
    """(value, line, passes, provisional) for one run, by the rule that applies to it."""
    fam, w = family(r["tag"])
    S = r["S_trailing200k"]
    if w == "nursery":
        crit = r["p3_criteria"]["survival"]
        return S, crit["threshold"], bool(r["p3_pass"]["pass"]), not r["finished"]
    if w == "home":
        return S, gate[r["agent"]], S >= gate[r["agent"]], not r["finished"]
    s = r["survivable"]
    return S, s["survival_line"], bool(s["pass"]), bool(s["provisional"]) or not r["finished"]


rows = {}                                         # (group index, world) -> {agent: point}
skipped = []
for r in runs:
    if r.get("S_trailing200k") is None:
        skipped.append(r); continue
    fam, w = family(r["tag"])
    gi = [g[1] for g in GROUPS].index(fam)
    rows.setdefault((gi, w), {})[r["agent"]] = point(r)
assert all(r["kind"] == "sequence" for r in skipped), [r["tag"] for r in skipped]

# display order inside a group: the design doc's concept order, then the tag order
ORDER = ["nursery", "home", "forage", "famine", "winter", "danger", "fog", "harsh",
         "danger_soft", "fog_soft", "harsh_soft",
         "danger_scout_a", "danger_scout_b", "danger_scout_c", "fog_scout_a", "fog_scout_b"]
assert all(w in ORDER for _, w in rows), [w for _, w in rows if w not in ORDER]


def verdict(gi, w, pts):
    if w == "home":
        return "above the gate so far" if all(p[2] for p in pts.values()) else "below the gate so far"
    if len(pts) == 1:
        a, p = next(iter(pts.items()))
        return f"{'passes' if p[2] else 'fails'} (only {a} agent run)"
    ok = {a: p[2] for a, p in pts.items()}
    if all(ok.values()):
        v = "passes, both"
        sl = RO["stage_lengths"].get(GROUPS[gi][1] + w) if GROUPS[gi][1] else None
        if sl and sl.get("too_easy"):
            v += "; flagged too easy"
    elif not any(ok.values()):
        v = "fails, both"
        base = w.replace("_soft", "")
        if w.endswith("_soft") and not any(p[2] for p in rows.get((0, base), {}).values()):
            v = "fails again: dropped"
    else:
        v = f"passes: {[a for a, o in ok.items() if o][0]} agent only"
    return v


lines = []                                       # (label, verdict, pts) or (group header,)
for gi, (gname, _) in enumerate(GROUPS):
    ws = sorted([w for g, w in rows if g == gi], key=ORDER.index)
    if not ws:
        continue
    lines.append((gname,))
    for w in ws:
        lines.append((label(w), verdict(gi, w, rows[(gi, w)]), rows[(gi, w)]))

# ---- draw ---------------------------------------------------------------------------------------
n = len(lines)
fig = plt.figure(figsize=(9.9, 0.30 * n + 1.5))
ax = fig.add_axes([0.235, 1.05 / (0.30 * n + 1.5), 0.49, 1 - 1.3 / (0.30 * n + 1.5)])
MARK = {"ordinary": "o", "modulated": "D"}
SIZE = {"ordinary": 7.5, "modulated": 6.2}
OFF = {"ordinary": 0.13, "modulated": -0.13}
xmax = math.ceil(max(p[0] for pts in rows.values() for p in pts.values()) / 50) * 50
ylab, yv, bold = [], [], []
n_fail = n_prov = n_pts = 0
for i, ln in enumerate(lines):
    y = n - 1 - i
    if len(ln) == 1:
        ylab.append(ln[0]); yv.append(y); bold.append(True)
        ax.axhline(y + 0.5, color=house.RULE, lw=0.6) if i else None
        continue
    lab, v, pts = ln
    ylab.append(lab); yv.append(y); bold.append(False)
    for a, (S, line, ok, prov) in pts.items():
        ax.plot([line, line], [y + OFF[a] - 0.2, y + OFF[a] + 0.2], color=house.TEXT_LIGHT, lw=1.4,
                solid_capstyle="butt", zorder=2)
        col = house.INK if ok else C.ACCENT
        ax.plot([S], [y + OFF[a]], marker=MARK[a], ms=SIZE[a], mec=col, mew=1.4,
                mfc="white" if prov else col, ls="none", zorder=3)
        n_pts += 1; n_fail += (not ok); n_prov += prov
    ax.text(1.02, y, v, transform=ax.get_yaxis_transform(), ha="left", va="center",
            fontsize=C.SMALLEST_PT, color=C.ACCENT if v.startswith("fails") else house.INK)
ax.set_yticks(yv); ax.set_yticklabels(ylab, fontsize=C.SMALLEST_PT)
for t, b in zip(ax.get_yticklabels(), bold):
    t.set_fontweight("bold" if b else "normal"); t.set_color(house.INK)
ax.set_ylim(-0.6, n - 0.4)
ax.set_xlim(0, xmax)
ax.tick_params(axis="y", length=0); ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.set_xlabel("survival: mean steps alive per episode over the run's last 200,000 episodes",
              fontsize=C.SMALLEST_PT + 1)
h = [Line2D([], [], marker="o", ms=7, color=house.INK, ls="none", label="ordinary agent"),
     Line2D([], [], marker="D", ms=6, color=house.INK, ls="none", label="modulated agent"),
     Line2D([], [], marker="o", ms=7, color=C.ACCENT, ls="none", label="below its line"),
     Line2D([], [], marker="o", ms=7, mfc="white", mec=house.INK, mew=1.4, ls="none", label="still training"),
     Line2D([], [], color=house.TEXT_LIGHT, lw=1.4, label="the agent's pass line")]
fig.legend(handles=h, loc="lower center", ncol=len(h), frameon=False, fontsize=C.SMALLEST_PT,
           bbox_to_anchor=(0.5, 0.0), handlelength=1.4, columnspacing=1.1)
C.assert_ticks_dont_collide(ax, "x")

# ---- data accounting ------------------------------------------------------------------------------
C.record_kind("p5_pilot_results", "training")
by = lambda gi: sum(len(p) for (g, _), p in rows.items() if g == gi)
avail = lambda pre: sum(1 for r in runs if family(r["tag"])[0] == pre and r.get("S_trailing200k") is not None)
nur_line = next(p[1] for (g, w), pts in rows.items() if w == "nursery" for p in pts.values())
relaunch = sum(1 for r in runs if r.get("attempt", 1) > 1 and family(r["tag"])[0] == GROUPS[2][1])
rec = [dict(what=f"runs: {GROUPS[gi][0].lower()}", used=by(gi), total=by(gi),
            note="every run of this group in the read-out; value = its last 200,000 episodes"
                 + (f"; {relaunch} of them are relaunches whose abandoned first attempts the read-out leaves out"
                    if gi == 2 and relaunch else ""))
       for gi in range(len(GROUPS)) if by(gi)]
rec.append(dict(what="runs: A-B-A-B pipeline checks (Pilot 2)", used=0, total=len(skipped),
                note="not drawn: they change world at every stage, so no single-world level exists; they are a plumbing check, not evidence"))
rec.append(dict(what="points still training (drawn hollow)", used=n_prov, total=n_pts,
                note="values from runs that had not ended when the read-out was written; may still move"))
rec.append(dict(what="points below their line (drawn red)", used=n_fail, total=n_pts,
                note=f"pilot worlds: half the agent's own Home survival; Nursery: {nur_line:g} steps; Home after Nursery: {GATE_FRAC:.0%} of the seed-42 Home level"))
C.record_samples("p5_pilot_results", rec)
print(f"  readout written {os.path.getmtime(C.READOUT):.0f}; {len(runs)} runs, {n_pts} points, gate {gate}")
C.save(fig, "p5_pilot_results", check_text=False)

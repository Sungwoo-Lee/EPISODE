#!/usr/bin/env python3
"""highlight.py - figures for the runs with the strongest animal- and injury-dependent bush dwell.

The cross-run page looks for the conditions where hiding depends most on the animal and on the
agent's injury, not for average trends. These figures present the selected runs only:

  rank          top training conditions (same world, setting, seed and test scenes) with BOTH agent types,
                ranked by the better agent's "both" score (the lower of its two percentile ranks: injury
                dependence -- the mean of the injury effect with no animal and with a wandering rabbit --
                and animal dependence -- the predator response); each row shows the ordinary and the
                modulated agent side by side, with those three effects and 95 % intervals
  pair --key K  one trained ordinary / modulated pair, per checkpoint across training: bush dwell
                unhurt vs injured in four scenes (no animal, wandering rabbit, chasing rabbit, predator)
  dose          the 22-Sep level-02 pair, tested at ten starting injuries: bush dwell against
                starting injury, per scene
  injtrain --key K   the B2 view at all ten starting injuries (0, 10, ..., 90): one line per injury
                across training, four scenes x two agents, for the level-04 or level-05 pair
  injdose  --key K   the same pair: bush dwell (mean over 2-10 M steps) against starting injury,
                four scenes, ordinary and modulated in one panel per scene

Numbers come from checkpoint_stats.py (ckpt_summary.csv, matched window 2-10 M steps, checkpoints
every 0.2 M) and from the dwell-sweep CSVs themselves. A temperature-set run was tested in eight
scene variants; the ranking uses its "neutral clean" variant only (comfortable air, no fire, no
sensory noise -- the variant closest to the core scenes), so one trained agent is one row.

    $P scripts/analysis/studies/f7b_across_runs/highlight.py --data results/analysis/f7b_across_runs \
        --fig-dir <dir> --figure rank|pair|dose [--key lvl05|lvl04]
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import collect as C  # noqa: E402  (read, ROOT)
import checkpoint_stats as K  # noqa: E402  (on_grid)
sys.path.insert(0, os.path.join(C.ROOT, "scripts", "analysis", "basic_behaviour"))
import _fig as FG  # noqa: E402

H = FG.H
UNHURT, INJURED = "#8a8f98", H.SERIES[0]
AGENT_COL = {"ordinary": "#8a8f98", "modulated": H.INK}   # B1: agent type in neutral inks (blue = injured, B2-B4)
AGENT_MK = {"ordinary": "o", "modulated": "s"}
LO_M, HI_M, SPACING_M = 2.0, 10.0, 0.2
SURVIVAL_FLOOR = 95.0
AV = "results/eval/avoidance"
PAIRS = {  # key -> (title, ordinary leaf, modulated leaf, scene set)
    "lvl05": ("level 05 (temperature world), tested in the neutral temperature scenes",
              f"{AV}/metrics_history_rppo_thermalprobe_neutral_clean/lvl05_control",
              f"{AV}/metrics_history_rppo_thermalprobe_neutral_clean/lvl05_modulated"),
    "lvl04": ("level 04, tested in the core scenes",
              f"{AV}/metrics_history_rppo_basicq2_wave2_blocking_bush/lvl04_control",
              f"{AV}/metrics_history_rppo_basicq2_wave2_blocking_bush/lvl04_modulated"),
}
INJ_GRID = {  # key -> (title, {agent: leaf for none / pred / rabbitwander}, {agent: leaf for the chasing rabbit})
    "lvl04": ("level 04 pair, core scenes",
              {"ordinary": f"{AV}/metrics_history_rppo_injurygrid_core/lvl04_control",
               "modulated": f"{AV}/metrics_history_rppo_injurygrid_core/lvl04_modulated"},
              {"ordinary": f"{AV}/metrics_history_rppo_injurygrid_chase_core/lvl04_control",
               "modulated": f"{AV}/metrics_history_rppo_injurygrid_chase_core/lvl04_modulated"}),
    "lvl05": ("level 05 pair, neutral temperature scenes",
              {"ordinary": f"{AV}/metrics_history_rppo_injurygrid_neutral_clean/lvl05_control",
               "modulated": f"{AV}/metrics_history_rppo_injurygrid_neutral_clean/lvl05_modulated"},
              {"ordinary": f"{AV}/metrics_history_rppo_injurygrid_chase_neutral_clean/lvl05_control",
               "modulated": f"{AV}/metrics_history_rppo_injurygrid_chase_neutral_clean/lvl05_modulated"}),
}
INJURIES = [f"{i:02d}" for i in range(0, 100, 10)]
DOSE = (f"{AV}/metrics_history_rppo_injurygrid_core/lvl02_control",
        f"{AV}/metrics_history_rppo_injurygrid_core/lvl02_modulated")
SCENE_ROWS = [("none", "no animal"), ("rabbitwander", "wandering rabbit"), ("rabbit", "chasing rabbit"),
              ("pred", "hunting predator")]


def series(leaf, scene, inj):
    d = C.read(leaf, scene, inj)
    return None if d is None else d.set_index("step")["bush_hiding"].astype(float) * 100.0


def episodes(leaf):
    import glob
    d = pd.read_csv(sorted(glob.glob(os.path.join(C.ROOT, leaf, "avoid_*_inj00.csv")))[0])   # any scene of this folder
    return int(d["n_episodes"].iloc[0]) if "n_episodes" in d.columns else 30


# ---------------------------------------------------------------- ranking table
def ranking(data):
    S = pd.read_csv(os.path.join(data, "ckpt_summary.csv"))
    S = S[S.window == "all"]
    L = pd.read_csv(os.path.join(data, "levels.csv"), dtype={"injury": str})
    L["injury"] = L["injury"].map(lambda x: f"{int(x):02d}")
    R = pd.read_csv(os.path.join(data, "runs.csv"))

    def low(pairs):
        m = np.zeros(len(L), bool)
        for s, i in pairs:
            m |= (L.scene == s) & (L.injury == i)
        return set(L[m & (L.survival_mean < SURVIVAL_FLOOR)].id)

    bad_state = low([("none", "00"), ("none", "70"), ("rabbitwander", "00"), ("rabbitwander", "70")])
    bad_anim = low([("none", "00"), ("pred", "00")])

    def g(q, f="mean"):
        return S[S.quantity == q].set_index("id")[f]

    T = pd.DataFrame({"inj": g("injury none"), "inj_lo": g("injury none", "lo"), "inj_hi": g("injury none", "hi"),
                      "inj_pos": g("injury none", "share_pos"),
                      "injw": g("injury rabbitwander"), "injw_lo": g("injury rabbitwander", "lo"),
                      "injw_hi": g("injury rabbitwander", "hi"),
                      "pred": g("animal pred"), "pred_lo": g("animal pred", "lo"), "pred_hi": g("animal pred", "hi"),
                      "wand": g("animal rabbitwander"), "jump": g("level none@00", "mean_abs_step")})
    T = T.join(R.set_index("id")[["family", "setting", "agent", "seed", "scene_set", "run_dir"]], how="inner")
    T = T[T.agent.isin(AGENT_COL)]
    T = T[(T.scene_set != "thermal") | T.setting.str.endswith("neutral clean")]
    n_all = len(T)
    T = T[~T.index.isin(bad_state | bad_anim)].dropna(subset=["inj", "injw", "pred"]).copy()
    T["state"] = (T.inj + T.injw) / 2
    T["both"] = np.minimum(T.state.rank(pct=True), T.pred.rank(pct=True))
    T["cond"] = T.family + " | " + T.setting + " | " + T.seed.astype(str) + " | " + T.scene_set
    paired = T.groupby("cond").agent.nunique() == 2
    T["paired"] = T.cond.map(paired)
    T["cond_score"] = T.cond.map(T.groupby("cond").both.max())
    return T.sort_values(["cond_score", "cond", "agent"], ascending=[False, True, True]), n_all


def conditions(T, top):
    """The top `top` conditions that have both agent types, best first: list of (cond, ordinary row, modulated row)."""
    P = T[T.paired]
    out = []
    for cond in dict.fromkeys(P.cond):
        g = P[P.cond == cond].set_index("agent")
        out.append((cond, g.loc["ordinary"], g.loc["modulated"]))
        if len(out) == top:
            break
    return out


def label(r, agent=True):
    s = r["setting"].replace("; scene variant neutral clean", " (neutral temperature scenes)")
    s = s.replace("; scene variant core", " (injury-grid core scenes)")
    fam = r["family"].replace(" (level 05)", "").replace(" (22 Sep)", "")
    return f"{fam}: {s}, " + (f"{r['agent']}, " if agent else "") + f"seed {int(r['seed'])}"


def fig_rank(data, top=10):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    T, n_all = ranking(data)
    C_ = conditions(T, top)[::-1]
    fig, axs = plt.subplots(1, 3, figsize=(12.0, 0.62 * len(C_) + 1.9), sharey=True)
    y = np.arange(len(C_))
    off = {"ordinary": 0.17, "modulated": -0.17}
    for ax, (m, lo, hi, xl) in zip(axs, (("inj", "inj_lo", "inj_hi",
                                         "injury effect, no animal:\ninjured (70) minus unhurt (0),\nbush dwell (pp)"),
                                        ("injw", "injw_lo", "injw_hi",
                                         "injury effect, wandering rabbit:\ninjured (70) minus unhurt (0),\nbush dwell (pp)"),
                                        ("pred", "pred_lo", "pred_hi",
                                         "animal effect: hunting predator\nminus no animal, unhurt,\nbush dwell (pp)"))):
        his = []
        for yi, (_, ro, rm) in zip(y, C_):
            for agent, r in (("ordinary", ro), ("modulated", rm)):
                c, yy = AGENT_COL[agent], yi + off[agent]
                ax.plot([r[lo], r[hi]], [yy, yy], color=c, lw=2.2, solid_capstyle="round")
                ax.plot(r[m], yy, AGENT_MK[agent], color=c, mfc=c if agent == "modulated" else H.PAPER,
                        ms=7.5, mew=1.6, zorder=3)
                his.append(r[hi])
            if yi > 0:
                ax.axhline(yi - 0.5, color=H.RULE, lw=0.7, zorder=0)
        ax.axvline(0, color=H.RULE, lw=1.1, zorder=0)
        ax.set_xlabel(xl, fontsize=H.FS_LABEL)
        ax.grid(axis="y", visible=False)
        los = [r[lo] for _, ro, rm in C_ for r in (ro, rm)]
        x0, x1 = min(-2, min(los) - 2), max(his) * 1.25 + 4      # room for the printed value
        ax.set_xlim(x0, x1)
        gap = 0.02 * (x1 - x0)                                    # one offset, the same in every panel
        for yi, (_, ro, rm) in zip(y, C_):
            for agent, r in (("ordinary", ro), ("modulated", rm)):
                ax.text(r[hi] + gap, yi + off[agent], f"{r[m]:+.0f}", va="center", fontsize=H.FS_LABEL - 1,
                        color=H.INK_2)
    axs[0].set_yticks(y)
    axs[0].set_yticklabels([label(ro, agent=False) for _, ro, _ in C_], fontsize=H.FS_LABEL - 1)
    axs[0].set_ylim(-0.6, len(C_) - 0.4)
    hs = [Line2D([], [], color=AGENT_COL[a], marker=AGENT_MK[a], mfc=AGENT_COL[a] if a == "modulated" else H.PAPER,
                 mew=1.6, lw=2.2, label=f"{a} agent (upper mark)" if a == "ordinary" else f"{a} agent (lower mark)")
          for a in AGENT_COL]
    fig.legend(handles=hs, loc="upper center", ncol=2, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.66, 1.0))
    fig.subplots_adjust(left=0.36, right=0.98, top=0.93, bottom=0.16 * 10 / len(C_), wspace=0.12)
    n_cond = T.cond.nunique()
    n_pair = T[T.paired].cond.nunique()
    rows = [{"what": "runs ranked (one per trained agent; temperature-set agents: neutral clean scenes only)",
             "used": len(T), "total": n_all,
             "note": "left out: the agent's average survival over the newest 20 checkpoints is under 95 of 100 steps "
                     "in a scene the measures use (no animal and wandering rabbit at injury 0 / 70, predator at injury 0)"},
            {"what": "conditions with both agent types ranked", "used": n_pair, "total": n_cond,
             "note": "a condition = same world, setting, seed and test scenes; conditions trained with only one agent "
                     "type, or with one agent left out above, are not shown"},
            {"what": "conditions shown", "used": len(C_), "total": n_pair,
             "note": f"the top {len(C_)} by the better agent's score"},
            {"what": "checkpoints per run", "used": 41, "total": 41,
             "note": "one per 0.2 M steps from 2 to 10 M (0.1 M-spaced runs: every second one)"}]
    return fig, rows


# ---------------------------------------------------------------- one pair across training
def fig_pair(key):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    title, leaf_o, leaf_m = PAIRS[key]
    fig, axs = plt.subplots(4, 2, figsize=(12.0, 11.0), sharex=True, sharey=True)
    rows = []
    for col, (agent, leaf) in enumerate((("ordinary", leaf_o), ("modulated", leaf_m))):
        base0 = series(leaf, "none", "00")
        for row, (sc, name) in enumerate(SCENE_ROWS):
            ax = axs[row, col]
            u, j = series(leaf, sc, "00"), series(leaf, sc, "70")
            for v, c, lab in ((u, UNHURT, "unhurt (injury 0)"), (j, INJURED, "injured (injury 70)")):
                x = v.index / 1e6
                ax.plot(x, v.values, color=c, lw=0.8, alpha=0.45)
                ax.plot(x, v.rolling(5, center=True, min_periods=3).mean().values, color=c, lw=2.2, label=lab)
            ax.axvspan(0, LO_M, color=H.RULE, alpha=0.25, lw=0, zorder=0)
            e = K.on_grid((j - u).dropna(), LO_M, HI_M, SPACING_M)
            txt = f"injured minus unhurt: {e.mean():+.0f} pp, positive at {100 * (e > 0).mean():.0f}% of checkpoints"
            if sc != "none":
                a = K.on_grid((u - base0).dropna(), LO_M, HI_M, SPACING_M)
                txt += f"\n{name} minus no animal (unhurt): {a.mean():+.0f} pp"
            ax.text(0.01, 0.97, txt, transform=ax.transAxes, va="top", fontsize=H.FS_LABEL - 1, color=H.INK,
                    path_effects=H.halo(width=3))
            if col == 0:
                ax.set_ylabel(f"{name}\nbush dwell (%)", fontsize=H.FS_LABEL)
            if row == 0:
                ax.set_title(f"{agent} agent", loc="left", fontsize=H.FS_BODY)
            rows.append({"what": f"{agent}, {name}: checkpoints (injury 0 and 70)", "used": int(min(len(u), len(j))),
                         "total": int(min(len(u), len(j))),
                         "note": f"every tested checkpoint drawn; the printed numbers use the {len(e)} on the 0.2 M grid "
                                 f"from {LO_M:g} to {HI_M:g} M steps; {episodes(leaf)} episodes per checkpoint"})
    for ax in axs[-1]:
        ax.set_xlabel("training (million steps)", fontsize=H.FS_LABEL)
    axs[0, 0].set_ylim(0, 132)            # 100-132: a label band above the data, so no line crosses the text
    axs[0, 0].set_yticks([0, 25, 50, 75, 100])
    axs[0, 0].set_xlim(0, 10)
    for ax in axs.flat:
        ax.axhline(100, color=H.RULE, lw=0.8, zorder=0)
    hs = [Line2D([], [], color=UNHURT, lw=2.2, label="unhurt (starting injury 0)"),
          Line2D([], [], color=INJURED, lw=2.2, label="injured (starting injury 70)"),
          Line2D([], [], color=H.INK_2, lw=0.8, alpha=0.6, label="thin: each checkpoint; thick: 5-checkpoint average"),
          Line2D([], [], color=H.RULE, lw=8, alpha=0.5, label="first 2 M steps: not used in the numbers")]
    fig.legend(handles=hs, loc="lower center", ncol=2, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.10, right=0.98, top=0.96, bottom=0.12, hspace=0.12, wspace=0.05)
    return fig, rows


# ---------------------------------------------------------------- injury dose response
def fig_dose():
    """Figure B4: the level-02 pair at ten starting injuries, in the B6 / B8 layout (no chasing-rabbit test)."""
    leaves = dict(zip(("ordinary", "modulated"), DOSE))
    return dose_figure(lambda agent, sc: leaves[agent], [r for r in SCENE_ROWS if r[0] != "rabbit"])


# ---------------------------------------------------------------- B2 at ten injuries
def grid_leaf(key, agent, scene):
    _, base, chase = INJ_GRID[key]
    return (chase if scene == "rabbit" else base)[agent]


def inj_colours():
    """Injury 0 in the B2/B3 'unhurt' grey; 10-90 on a blue ramp no lighter than #86b4e7 (about 2:1 on the page,
    darker than the gridlines -- register F81), anchored so injury 70 is the house blue B2/B3 use for 'injured'."""
    from matplotlib.colors import LinearSegmentedColormap
    ramp = LinearSegmentedColormap.from_list("inj", [(0.0, "#86b4e7"), (0.75, H.BLUE), (1.0, "#123f77")])
    out = {"00": UNHURT}
    for k, i in enumerate(INJURIES[1:]):
        out[i] = ramp(k / (len(INJURIES) - 2))
    return out


def fig_injtrain(key):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    title = INJ_GRID[key][0]
    col = inj_colours()
    fig, axs = plt.subplots(4, 2, figsize=(12.0, 11.0), sharex=True, sharey=True)
    rows = []
    for c, agent in enumerate(("ordinary", "modulated")):
        for r, (sc, name) in enumerate(SCENE_ROWS):
            ax = axs[r, c]
            leaf = grid_leaf(key, agent, sc)
            ends = {}
            n_ck = []
            for i in INJURIES:
                v = series(leaf, sc, i)
                if v is None:
                    raise SystemExit(f"missing {leaf}/avoid_{sc}_inj{i}.csv -- run the injury-grid sweep first")
                ax.plot(v.index / 1e6, v.rolling(5, center=True, min_periods=3).mean().values, color=col[i],
                        lw=2.0 if i in ("00", "90") else 1.3, zorder=3 if i in ("00", "90") else 2)
                ends[i] = K.on_grid(v, LO_M, HI_M, SPACING_M).mean()
                n_ck.append(len(v))
            ax.axvspan(0, LO_M, color=H.RULE, alpha=0.25, lw=0, zorder=0)
            ax.axhline(100, color=H.RULE, lw=0.8, zorder=0)
            ax.text(0.01, 0.97, f"mean over 2\u201310 M steps: injury 0 \u2192 {ends['00']:.0f}%, "
                                f"injury 50 \u2192 {ends['50']:.0f}%, injury 90 \u2192 {ends['90']:.0f}%",
                    transform=ax.transAxes, va="top", fontsize=H.FS_LABEL - 1, color=H.INK,
                    path_effects=H.halo(width=3))
            if c == 0:
                ax.set_ylabel(f"{name}\nbush dwell (%)", fontsize=H.FS_LABEL)
            if r == 0:
                ax.set_title(f"{agent} agent", loc="left", fontsize=H.FS_BODY)
            rows.append({"what": f"{agent}, {name}: checkpoints per starting injury (10 injuries)",
                         "used": int(min(n_ck)), "total": int(max(n_ck)),
                         "note": f"every tested checkpoint drawn (5-checkpoint average); the printed means use the "
                                 f"0.2 M grid from {LO_M:g} to {HI_M:g} M steps; {episodes(leaf)} episodes per checkpoint"})
    for ax in axs[-1]:
        ax.set_xlabel("training (million steps)", fontsize=H.FS_LABEL)
    axs[0, 0].set_ylim(0, 118)
    axs[0, 0].set_yticks([0, 25, 50, 75, 100])
    axs[0, 0].set_xlim(0, 10)
    hs = [Line2D([], [], color=col[i], lw=2.0 if i in ("00", "90") else 1.3, label=f"injury {int(i)}") for i in INJURIES]
    hs.append(Line2D([], [], color=H.RULE, lw=8, alpha=0.5, label="first 2 M steps: not in the means"))
    fig.legend(handles=hs, loc="lower center", ncol=6, frameon=False, fontsize=H.FS_LABEL - 1, bbox_to_anchor=(0.5, -0.01),
               title="starting injury of the test (grey = unhurt, light to dark blue = injury 10 to 90); each line averages 5 checkpoints",
               title_fontsize=H.FS_LABEL - 1)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.96, bottom=0.115, hspace=0.12, wspace=0.05)
    return fig, rows


def dose_figure(leaf_of, scenes):
    """Panels = scenes; open grey circle = ordinary, filled black square = modulated; 0-100 % in every panel.
    The layout shared by Figures B4, B6 and B8, so the three read the same way."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    fig, axs = plt.subplots(1, len(scenes), figsize=(2.35 * len(scenes) + 0.9, 3.9), sharey=True)
    rows = []
    x = [int(i) for i in INJURIES]
    for ax, (sc, name) in zip(axs, scenes):
        for agent in ("ordinary", "modulated"):
            leaf = leaf_of(agent, sc)
            m, lo, hi = [], [], []
            for i in INJURIES:
                v = K.on_grid(series(leaf, sc, i), LO_M, HI_M, SPACING_M)
                p = C.P.W.window_profile(v.to_numpy(), windows=[len(v)]).iloc[0]
                m.append(p["mean"]); lo.append(p["lo"]); hi.append(p["hi"])
            c = AGENT_COL[agent]
            ax.fill_between(x, lo, hi, color=c, alpha=0.10 if agent == "ordinary" else 0.16, lw=0)
            for edge in (lo, hi):
                ax.plot(x, edge, color=c, lw=0.7, ls=(0, (3, 2)))
            ax.plot(x, m, color=c, lw=2.2, marker=AGENT_MK[agent], ms=5.5,
                    mfc=c if agent == "modulated" else H.PAPER, mew=1.4, zorder=3)
            rows.append({"what": f"{agent}, {name}: checkpoints per starting injury", "used": len(v), "total": len(v),
                         "note": f"0.2 M grid from {LO_M:g} M to the last tested checkpoint ({v.index.max() / 1e6:.1f} M); "
                                 f"{episodes(leaf)} episodes per checkpoint"})
        ax.set_title(name, loc="left", fontsize=H.FS_BODY)
        ax.set_xticks([0, 30, 60, 90])
        ax.set_xlim(-4, 94)
        ax.set_xlabel("starting injury", fontsize=H.FS_LABEL)
    axs[0].set_ylabel("bush dwell (%),\nmean over 2\u201310 M steps", fontsize=H.FS_LABEL)
    axs[0].set_ylim(0, 100)
    hs = [Line2D([], [], color=AGENT_COL[a], marker=AGENT_MK[a], mfc=AGENT_COL[a] if a == "modulated" else H.PAPER,
                 mew=1.4, lw=2.2, label=f"{a} agent") for a in AGENT_COL]
    hs.append(Line2D([], [], color=H.INK_2, lw=0.7, ls=(0, (3, 2)), label="dashed edges: 95 % interval, in the line's tone"))
    fig.legend(handles=hs, loc="lower center", ncol=3, frameon=False, fontsize=H.FS_LABEL - 1, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.10 if len(scenes) == 4 else 0.12, right=0.99, top=0.89, bottom=0.30, wspace=0.08)
    return fig, rows


def fig_injdose(key):
    return dose_figure(lambda agent, sc: grid_leaf(key, agent, sc), SCENE_ROWS)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--fig-dir", required=True)
    ap.add_argument("--figure", required=True, choices=["rank", "pair", "dose", "injtrain", "injdose"])
    ap.add_argument("--key", choices=list(PAIRS))
    a = ap.parse_args(argv)
    H.apply()
    if a.figure == "rank":
        fig, rows = fig_rank(a.data)
        stem = "f7b_hl_rank"
    elif a.figure == "pair":
        if not a.key:
            raise SystemExit("--figure pair needs --key")
        fig, rows = fig_pair(a.key)
        stem = f"f7b_hl_pair__{a.key}"
    elif a.figure in ("injtrain", "injdose"):
        if not a.key:
            raise SystemExit(f"--figure {a.figure} needs --key")
        fig, rows = (fig_injtrain if a.figure == "injtrain" else fig_injdose)(a.key)
        stem = f"f7b_hl_{a.figure}__{a.key}"
    else:
        fig, rows = fig_dose()
        stem = "f7b_hl_dose"
    FG.record_samples(os.path.abspath(a.fig_dir), stem, rows)
    FG.save(fig, os.path.abspath(a.fig_dir), stem)


if __name__ == "__main__":
    main()

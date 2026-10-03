#!/usr/bin/env python3
"""figures.py - the figures of the "Figure 7b across runs" page, from collect.py's tables.

    $P scripts/analysis/studies/f7b_across_runs/figures.py --data results/analysis/f7b_across_runs \
        --fig-dir docs/experiments/active/hypervigilance/f7b_across_runs/figures --figure rank|family|levels --group G

  rank    injury effect (bush dwell at start injury 70 minus 0) in the two rabbit scenes, one dot per
          run x scene set, sorted, with the no-animal scene's injury effect for the same run beside it
  family  the same injury effect grouped by setting family (rows), agent as marker shape
  levels  the Figure 7b view itself for one group of runs: late-training bush dwell per scene at
          injury 0 (hollow) and 70 (filled), one row per run
Every figure writes <stem>.samples.json (data used / available) via _fig.record_samples.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "basic_behaviour"))
import _fig as FG  # noqa: E402

H = FG.H
SET_ORDER = ["july", "core_old", "core", "thermal", "injgrid", "world"]
SET_COL = dict(zip(SET_ORDER, ["#a3782f", "#7fb0e6", H.SERIES[0], H.SERIES[1], "#8a6fb3", H.SERIES[2]]))
SET_SHORT = {"july": "July set (animals can enter the bush)",
             "core_old": "core set, before the fix (animals can enter the bush)",
             "core": "core set (bush blocks animals)",
             "thermal": "temperature set (8 fire/ambient variants)", "injgrid": "injury-grid set (3 scenes)",
             "world": "training-world set (campfire by the bush)"}
SET_TAG = {"july": "July set", "core_old": "core set, before fix", "core": "core set", "thermal": "temperature set", "injgrid": "injury-grid set",
           "world": "own-world set"}
AG_MK = {"ordinary": "o", "modulated": "^"}
SHORT_SCENE = {"none": "no animal", "pred": "hunting predator", "rabbit": "chasing rabbit",
               "rabbit_olfzero": "chasing rabbit,\nno smell", "rabbitwander": "wandering rabbit",
               "rabbitwander_predsmell": "predator-smelling\nrabbit"}
SCENES = list(SHORT_SCENE)
LEVEL_SCENE = {"none": "no\nanimal", "pred": "hunting\npredator", "rabbit": "chasing\nrabbit",
               "rabbit_olfzero": "chasing rabbit,\nno smell", "rabbitwander": "wandering\nrabbit",
               "rabbitwander_predsmell": "predator-\nsmelling rabbit"}
QUANT = [("rabbit", "chasing rabbit: injury effect"),
         ("rabbit-minus-none", "chasing rabbit: injury effect minus\nthe no-animal scene's injury effect"),
         ("rabbitwander", "wandering rabbit: injury effect"),
         ("rabbitwander-minus-none", "wandering rabbit: injury effect minus\nthe no-animal scene's injury effect")]
YLAB = "injury 70 minus injury 0,\nbush dwell (percentage points)"
GROUPS = {  # page group -> (title, families)
    "july": ("July runs (levels 03-04)", ["July network size", "July level-04 variants", "July GAE return",
                                          "July early modulator"]),
    "core_old": ("Curriculum wave 1, core scenes tested before the bush fix", ["Curriculum wave 1"]),
    "core": ("Blocking-bush training, core scenes", ["Blocking-bush training"]),
    "thermal": ("Blocking-bush training, levels 05-06, temperature scenes", ["Blocking-bush training"]),
    "injgrid": ("Blocking-bush training, injury-grid scenes", ["Blocking-bush training"]),
    "smell": ("Smell study, level 05", ["Smell study (level 05)"]),
    "body": ("Body rules, level 05", ["Body rules (level 05)"]),
    "thirst": ("Thirst task", ["Thirst task"]),
}
GROUP_SET = {"july": "july", "core_old": "core_old", "core": "core", "thermal": "thermal", "injgrid": "injgrid", "smell": "world",
             "body": "world", "thirst": "world"}
FAMILY_ORDER = [f for g in GROUPS.values() for f in g[1]]
FAMILY_ORDER = list(dict.fromkeys(FAMILY_ORDER))


def load(d):
    R = pd.read_csv(os.path.join(d, "runs.csv"))
    L = pd.read_csv(os.path.join(d, "levels.csv"), dtype={"injury": str})
    E = pd.read_csv(os.path.join(d, "injury_effect.csv"))
    X = pd.read_csv(os.path.join(d, "dropped.csv"))
    L["injury"] = L["injury"].map(lambda x: f"{int(x):02d}")
    return R, L, E, X


BODY_CODE = "HCWF"   # hunger slows healing, healing Costs food, Warmth costs food, scarcer Food


HOLLOW_NOTE = ("hollow: in a scene this value uses, the agent's average survival over the newest 20 "
               "checkpoints is under 95 of 100 steps, so bush dwell is a share of a shortened episode")


def hollow_handle():
    from matplotlib.lines import Line2D
    return Line2D([], [], ls="", marker="o", ms=8, color=H.INK_2, mfc=H.PAPER, mew=1.4,
                  label="hollow: agent died early in a scene used (not interpreted)")


SURVIVAL_FLOOR = 95.0   # the Basic Behaviour page's rule: below it a value is reported, not interpreted


def short_ids(L, scenes):
    """Runs whose late-window survival is under the floor in any of these scenes, at either injury."""
    s = L[L.scene.isin(scenes) & (L.survival_mean < SURVIVAL_FLOOR)]
    return set(s["id"])


def flagged(L, q):
    base = q.split("-minus-")[0]
    return short_ids(L, [base, "none"] if "minus" in q else [base])


def row_label(r):
    st, fam = r["setting"], r["family"]
    if fam == "Body rules (level 05)":
        w = st.split(":")[0]
        on = "".join(c for b, c in zip(w[1:], BODY_CODE) if b == "1") or "none"
        st = f"{w}  rules on: {on}"
    elif r["scene_set"] in ("thermal", "injgrid"):
        lvl, var = st.split("; scene variant ")
        st = f"{lvl.replace('level ', 'L')} · {var}"
    elif fam == "Smell study (level 05)":
        st = st.replace(" smell", "").replace(" (control)", " (control)") + f" · seed {int(r['seed'])}"
    elif fam.startswith("July"):
        st = st.replace("network size ", "size ").replace(", early modulator design", "")
        st = f"{ {'July network size': 'size', 'July level-04 variants': 'L04 variant', 'July GAE return': 'GAE', 'July early modulator': 'early modulator'}[fam] }: {st}"
    elif r["scene_set"] in ("core", "core_old"):
        st = st.split(",")[0]
    return f"{st} · {r['agent']}"


def ckpt_rows(R, what, extra=()):
    rows = []
    for s in SET_ORDER:
        g = R[R.scene_set == s]
        if len(g):
            rows.append({"what": f"{what}, {SET_SHORT[s]}: checkpoints summarised (newest 20 per run)",
                         "used": 20 * len(g), "total": int(g.n_ckpt.sum()),
                         "note": f"{len(g)} run × scene-set rows; older checkpoints are not summarised"})
    rows.append({"what": "episodes behind each checkpoint value", "used": 30, "total": 30,
                 "note": "30 evaluation episodes per checkpoint, scene and start injury"})
    return rows + list(extra)


def zero(ax):
    ax.axvline(0, color=H.RULE, lw=1.1, zorder=0) if ax.name == "rectilinear" else None


def fig_rank(R, L, E, X):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    fig, axs = plt.subplots(2, 2, figsize=(12.0, 9.6), sharey=True)
    rows = []
    nn = E[E.scene == "none"].set_index("id")["mean"]
    for ax, (q, qname) in zip(axs.T.ravel(), QUANT):
        e = E[E.scene == q].merge(R, on="id").sort_values("mean").reset_index(drop=True)
        fl = flagged(L, q)
        for i, r in e.iterrows():
            c = SET_COL[r["scene_set"]]
            ax.plot([i, i], [r["lo"], r["hi"]], color=c, lw=0.9, alpha=0.5)
            ax.plot(i, r["mean"], ls="", marker=AG_MK[r["agent"]], ms=4.5, color=c,
                    mfc=H.PAPER if r["id"] in fl else c, mew=1.2)
            if "minus" not in q and r["id"] in nn.index:
                ax.plot(i, nn[r["id"]], ls="", marker="_", ms=6, mew=1.4, color=H.INK)
        ax.axhline(0, color=H.RULE, lw=1.1, zorder=0)
        ax.set_xlim(-1, len(e))
        ax.set_xticks([])
        ax.set_xlabel(f"runs, sorted by this quantity ({len(e)} rows)", fontsize=H.FS_LABEL)
        ax.set_title(qname, loc="left", fontsize=H.FS_LABEL + 1)
        ax.grid(axis="x", visible=False)
        rows.append({"what": f"{qname.replace(chr(10), ' ')}: values shown hollow (not interpreted)",
                     "used": int(e["id"].isin(fl).sum()), "total": len(e), "note": HOLLOW_NOTE})
        rows.append({"what": f"{qname.replace(chr(10), ' ')}: rows with a summarised value", "used": len(e),
                     "total": len(R), "note": "all rows" if len(e) == len(R) else
                     "the injury-grid scene set has no chasing rabbit"})
    for ax in axs[:, 0]:
        ax.set_ylabel(YLAB, fontsize=H.FS_LABEL)
    axs[0, 0].set_ylim(-32, 42)
    hs = [Line2D([], [], ls="", marker="s", ms=8, color=SET_COL[s], label=SET_SHORT[s]) for s in SET_ORDER]
    hs += [Line2D([], [], ls="", marker=AG_MK[a], ms=8, color=H.INK_2, label=f"{a} agent") for a in AG_MK]
    hs += [hollow_handle()]
    hs += [Line2D([], [], ls="", marker="_", ms=9, mew=1.6, color=H.INK, label="same run, no-animal scene"),
           Line2D([], [], color=H.INK_2, lw=1.0, label="95% interval (checkpoint-to-checkpoint)")]
    fig.legend(handles=hs, loc="lower center", ncol=3, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.12, 1, 1), h_pad=1.4, w_pad=1.0)
    return fig, ckpt_rows(R, "all rows") + rows


def fig_family(R, L, E, X):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    fams = [f for f in FAMILY_ORDER if f in set(R.family)]
    keys = [(f, s) for f in fams for s in SET_ORDER if ((R.family == f) & (R.scene_set == s)).any()]
    h = 2 * (0.42 * len(keys) + 1.0) + 1.2
    fig, axs = plt.subplots(2, 2, figsize=(12.0, h), sharey=True, sharex=True)
    rng = np.random.default_rng(0)
    for ax, (q, qname) in zip(axs.ravel(), QUANT):
        e = E[E.scene == q].merge(R, on="id")
        fl = flagged(L, q)
        for k, (f, s) in enumerate(keys):
            g = e[(e.family == f) & (e.scene_set == s)]
            y = len(keys) - 1 - k
            for _, r in g.iterrows():
                yy = y + rng.uniform(-0.22, 0.22)
                ax.plot([r["lo"], r["hi"]], [yy, yy], color=SET_COL[s], lw=0.8, alpha=0.4)
                ax.plot(r["mean"], yy, ls="", marker=AG_MK[r["agent"]], ms=5, color=SET_COL[s], alpha=0.9,
                        mfc=H.PAPER if r["id"] in fl else SET_COL[s], mew=1.2)
            if len(g):
                ax.plot([g["mean"].mean()] * 2, [y - 0.34, y + 0.34], color=H.INK, lw=2.0)
            elif ((R.family == f) & (R.scene_set == s)).any():
                ax.text(0, y, "  no such scene in this set", va="center", ha="left", fontsize=H.FS_LABEL - 1,
                        color=H.INK_2)
        ax.axvline(0, color=H.RULE, lw=1.1, zorder=0)
        ax.set_xlim(-35, 40)
        ax.tick_params(axis="x", labelbottom=True)
        ax.set_title(qname, loc="left", fontsize=H.FS_LABEL + 1)
        ax.grid(axis="y", visible=False)
    for ax in axs[:, 0]:
        ax.set_yticks(range(len(keys)))
        ax.set_yticklabels([f"{f} · {SET_TAG[s]}" for f, s in keys][::-1], fontsize=H.FS_LABEL)
        ax.set_ylim(-0.6, len(keys) - 0.4)
    for ax in axs[1]:
        ax.set_xlabel(YLAB.replace("\n", " "), fontsize=H.FS_LABEL)
    hs = [Line2D([], [], ls="", marker="s", ms=8, color=SET_COL[s], label=SET_SHORT[s]) for s in SET_ORDER]
    hs += [Line2D([], [], ls="", marker=AG_MK[a], ms=8, color=H.INK_2, label=f"{a} agent") for a in AG_MK]
    hs += [Line2D([], [], color=H.INK, lw=2.0, label="mean of the rows in the group (hollow included)"),
           hollow_handle()]
    fig.legend(handles=hs, loc="lower center", ncol=3, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.005))
    fig.tight_layout(rect=(0, 1.15 / h, 1, 1), h_pad=1.2, w_pad=1.0)
    return fig, ckpt_rows(R, "all rows")


BODY = ["hunger slows healing", "healing costs food", "warmth costs food", "scarcer food"]


def within_groups(R):
    """(panel title, [(row label, ids)]) for each family with a setting that varies inside it."""
    out = []
    b = R[R.family == "Body rules (level 05)"]
    rows = []
    for k, name in enumerate(BODY):
        for v, word in (("1", "on"), ("0", "off")):
            ids = b[b.setting.str[1 + k] == v]["id"].tolist()
            if v == "0":   # w0000 (all off) is the smell study's control seed 42 pair; not double-counted here
                pass
            rows.append((f"{name}: {word}", ids))
    out.append(("Body rules, level 05 (each rule on vs off; 15 worlds × 2 agents)", rows))
    sm = R[R.family == "Smell study (level 05)"]
    out.append(("Smell study, level 05 (3 seeds × 2 agents per world)",
                [(w, sm[sm.setting == w]["id"].tolist()) for w in
                 ["two-channel smell (control)", "single-channel smell", "matched-strength smell"]]))
    th = R[R.family == "Thirst task"]
    rows = [(f"{m}x{m} map", th[th.setting.str.startswith(f"{m}x{m}")]["id"].tolist()) for m in (10, 15, 20)]
    rows += [(lab, th[th.setting.str.endswith(suf)]["id"].tolist()) for lab, suf in
             (("smell across the map", "across the map"), ("smell range 5", "range 5"), ("smell range 3", "range 3"))]
    out.append(("Thirst task (map size, then smell range; 9 worlds × 2 agents)", rows))
    w1 = R[R.family == "Curriculum wave 1"]
    out.append(("Curriculum wave 1, core scenes tested before the bush fix (1 run per level and agent)",
                [(f"level 0{l}", w1[w1.setting == f"level 0{l}"]["id"].tolist()) for l in (2, 3, 4)]))
    t = R[(R.scene_set == "thermal")]
    vs = sorted(t.setting.str.split("scene variant ").str[1].unique())
    out.append(("Blocking-bush training, levels 05-06, temperature scenes (variant of the scene)",
                [(v, t[t.setting.str.endswith(v)]["id"].tolist()) for v in vs]))
    return out


def fig_within(R, L, E, X):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    G = within_groups(R)
    n_rows = [len(rows) for _, rows in G]
    h = sum(0.36 * n + 0.9 for n in n_rows) + 1.0
    fig, axs = plt.subplots(len(G), 2, figsize=(12.0, h), sharex=True,
                            gridspec_kw={"height_ratios": [n + 1.2 for n in n_rows]})
    qs = [QUANT[0], QUANT[1]]
    for gi, (title, rows) in enumerate(G):
        for qi, (q, qname) in enumerate(qs):
            ax = axs[gi, qi]
            e = E[E.scene == q].merge(R[["id", "agent", "scene_set"]], on="id").set_index("id")
            fl = flagged(L, q)
            for k, (lab, ids) in enumerate(rows):
                y = len(rows) - 1 - k
                g = e.loc[[i for i in ids if i in e.index]]
                for j, (_, r) in enumerate(g.iterrows()):
                    yy = y + (j - (len(g) - 1) / 2) * min(0.08, 0.6 / max(len(g), 1))
                    c = SET_COL[r["scene_set"]]
                    ax.plot(r["mean"], yy, ls="", marker=AG_MK[r["agent"]], ms=4.8, color=c, alpha=0.85,
                            mfc=H.PAPER if r.name in fl else c, mew=1.1)
                if len(g):
                    ax.plot([g["mean"].mean()] * 2, [y - 0.36, y + 0.36], color=H.INK, lw=2.0)
            ax.axvline(0, color=H.RULE, lw=1.1, zorder=0)
            ax.set_yticks(range(len(rows)))
            ax.set_yticklabels([lab for lab, _ in rows][::-1] if qi == 0 else [], fontsize=H.FS_LABEL)
            ax.set_ylim(-0.6, len(rows) - 0.4)
            ax.grid(axis="y", visible=False)
            ax.set_xlim(-30, 35)
            ax.tick_params(axis="x", labelbottom=True)
            ax.set_title((title + "\n" if qi == 0 else "\n") + qname.replace("\n", " "), loc="left",
                         fontsize=H.FS_LABEL)
    for ax in axs[-1]:
        ax.set_xlabel(YLAB.replace("\n", " "), fontsize=H.FS_LABEL)
    hs = [Line2D([], [], ls="", marker=AG_MK[a], ms=8, color=H.INK_2, label=f"{a} agent") for a in AG_MK]
    hs += [Line2D([], [], color=H.INK, lw=2.0, label="mean of the runs in the row (hollow included)"),
           hollow_handle()]
    hs += [Line2D([], [], ls="", marker="s", ms=8, color=SET_COL[k], label=SET_SHORT[k]) for k in ("core_old", "thermal", "world")]
    fig.legend(handles=hs, loc="lower center", ncol=2, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.003))
    fig.tight_layout(rect=(0, 1.15 / h, 1, 1), h_pad=1.0, w_pad=1.0)
    rows = [{"what": f"{t.split(' (')[0]}: runs", "used": len({i for _, ids in r for i in ids}),
             "total": len({i for _, ids in r for i in ids}), "note": "every selected run of the family"}
            for t, r in G]
    return fig, ckpt_rows(R[R.id.isin({i for _, r in G for _, ids in r for i in ids})], "runs in this figure") + rows


def fig_levels(R, L, E, X, group):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    title, fams = GROUPS[group]
    sset = GROUP_SET[group]
    G = R[R.family.isin(fams) & (R.scene_set == sset)].copy()
    G["fo"] = G.family.map(fams.index)
    G = G.sort_values(["fo", "setting", "agent", "seed"]).reset_index(drop=True)
    scenes = [s for s in SCENES if G.scenes.str.contains(rf"(^|,){s}(,|$)").any()]
    n = len(G)
    fig, axs = plt.subplots(1, len(scenes), figsize=(12.0, 0.27 * n + 2.3), sharey=True)
    axs = np.atleast_1d(axs)
    short = short_ids(L, [s for s in scenes if s != "pred"])   # a predator ending the episode is the scene working
    lab = [row_label(r) + ("  *" if r["id"] in short else "") for _, r in G.iterrows()]
    for ax, s in zip(axs, scenes):
        sub = L[(L.scene == s)].set_index(["id", "injury"])
        for i, r in G.iterrows():
            y = n - 1 - i
            try:
                a, b = sub.loc[(r["id"], "00")], sub.loc[(r["id"], "70")]
            except KeyError:
                continue
            ax.plot([a["mean"], b["mean"]], [y, y], color=H.INK_2, lw=1.0, alpha=0.6)
            ax.plot(b["mean"], y, ls="", marker=AG_MK[r["agent"]], ms=5.5, color=H.INK, zorder=3)
            ax.plot(a["mean"], y, ls="", marker=AG_MK[r["agent"]], ms=7.0, color=H.INK_2, mfc="none",
                    mew=1.3, zorder=4)   # drawn on top so a coinciding injury-0 value stays visible
        for i in range(1, n):
            if G.family[i] != G.family[i - 1]:
                ax.axhline(n - i - 0.5, color=H.RULE, lw=1.0)
        ax.set_xlim(-5, 105)
        ax.set_xticks([0, 50, 100])
        ax.set_xticks([25, 75], minor=True)
        ax.set_xticklabels(["0", "50", "100"], fontsize=H.FS_LABEL - 1)
        ax.grid(axis="x", which="both", color=H.RULE, lw=0.6, alpha=0.7)
        ax.set_title(LEVEL_SCENE[s], loc="center", fontsize=H.FS_LABEL)
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="x", which="minor", length=0)
    axs[0].set_yticks(range(n))
    axs[0].set_yticklabels(lab[::-1], fontsize=H.FS_LABEL - 1)
    axs[0].set_ylim(-0.7, n - 0.3)
    h = 0.27 * n + 2.3
    fig.supxlabel("bush dwell, newest 20 checkpoints: share of the scene's steps on the bush (%)",
                  fontsize=H.FS_BODY, y=0.62 / h)
    hs = [Line2D([], [], ls="", marker="o", ms=8, color=H.INK_2, mfc="none", mew=1.3, label="start injury 0 (hollow)"),
          Line2D([], [], ls="", marker="o", ms=8, color=H.INK, label="start injury 70 (filled)"),
          Line2D([], [], ls="", marker="o", ms=8, color=H.INK_2, mfc=H.PAPER, label="ordinary agent (circle)"),
          Line2D([], [], ls="", marker="^", ms=8, color=H.INK_2, mfc=H.PAPER, label="modulated agent (triangle)")]
    fig.legend(handles=hs, loc="lower center", ncol=4, frameon=False, fontsize=H.FS_LABEL, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.85 / h, 1, 1), w_pad=1.2)
    return fig, ckpt_rows(G, title) + [{"what": "runs marked * (agent died early in at least one scene)",
                                        "used": int(G["id"].isin(short).sum()), "total": len(G),
                                        "note": "* = average survival under 95 of 100 steps in at least one predator-free "
                                                "scene and injury; read that run's values with care"}]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--fig-dir", required=True)
    ap.add_argument("--figure", required=True, choices=["rank", "family", "within", "levels"])
    ap.add_argument("--group", choices=list(GROUPS))
    a = ap.parse_args(argv)
    H.apply()
    D = load(a.data)
    if a.figure == "levels":
        if not a.group:
            raise SystemExit("--figure levels needs --group")
        fig, rows = fig_levels(*D, a.group)
        stem = f"f7b_levels__{a.group}"
    else:
        fig, rows = {"rank": fig_rank, "family": fig_family, "within": fig_within}[a.figure](*D)
        stem = f"f7b_{a.figure}"
    FG.record_samples(os.path.abspath(a.fig_dir), stem, rows)
    FG.save(fig, os.path.abspath(a.fig_dir), stem)


if __name__ == "__main__":
    main()

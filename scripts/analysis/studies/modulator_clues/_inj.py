"""Data access for the injury-dependence main body of the page.

Plan: docs/experiments/active/modulator_clues/INJURY_DEPENDENCE_PLAN.md. Sources:
  results/eval/avoidance/metrics_history_rppo_injurygrid_<version>/   injury-grid scene sweeps (A)
  results/analysis/injury_dependence/manip/                            live input manipulation (B)
  results/analysis/injury_dependence/replay/                           replay manipulation (C3)
  results/analysis/injury_dependence/dose/{final,late}/                training-world dose scans (C)
"""
import glob, json, os
import numpy as np
import _common as C

ID = os.path.join(C.ROOT, "results/analysis/injury_dependence")
EV = os.path.join(C.ROOT, "results/eval/avoidance")
LEVELS = ["lvl02", "lvl03", "lvl04", "lvl05", "lvl06"]
INJ = list(range(0, 100, 10))
ARMS_T = ("neutral", "cool", "fire_by_bush", "fire_away")
VERSIONS = {"lvl02": ["core"], "lvl03": ["core"], "lvl04": ["core"],
            "lvl05": [f"{a}_clean" for a in ARMS_T],
            "lvl06": [f"{a}_{b}" for a in ARMS_T for b in ("clean", "noise_matched")]}
VERSION_NAME = {"core": "", "neutral": "comfortable", "cool": "cool", "fire_by_bush": "fire by bush",
                "fire_away": "fire away"}
SCENES = [("avoid_none", "no animal"), ("avoid_pred", "predator"), ("avoid_rabbitwander", "wandering rabbit")]
MIN_DEN = 2000                   # a dose-scan bin needs this many decisions to be drawn
LAST = 20                        # scene measures: mean over the newest 20 checkpoints


def version_label(v):
    if v == "core":
        return ""
    arm = v.replace("_clean", "").replace("_noise_matched", "")
    return VERSION_NAME[arm] + (", noise" if v.endswith("noise_matched") else "")


# ------------------------------------------------------------------ training-world dose scans
def dose(label, which="final"):
    """{reading: {measure: array(2 pred_near, 10 bins, 2 [num, den])}} or None."""
    if which == "final":
        p = os.path.join(ID, "dose/final", f"{label}.json")
        if not os.path.exists(p):
            return None
        return _tallies(json.load(open(p)))
    out = []
    for p in sorted(glob.glob(os.path.join(ID, "dose/late", f"{label}_*.json"))):
        out.append(_tallies(json.load(open(p))))
    return out or None


def _tallies(d):
    if d.get("max_blocks") is not None:
        raise ValueError(f"{d['run']}: dose scan was a partial test (--max-blocks); rerun in full")
    return {r: {m: np.asarray(v) for m, v in ms.items()} for r, ms in d["tallies"].items()}


def rate(t, pred_near=0):
    """Percentage per bin from a (2, bins, 2) tally, NaN where the denominator is below MIN_DEN."""
    num, den = t[pred_near, :, 0], t[pred_near, :, 1]
    r = 100.0 * num / np.maximum(den, 1)
    r[den < MIN_DEN] = np.nan
    return r, den


# ------------------------------------------------------------------ scene sweeps
def scene_series(version, label, scene, inj, measure="bush_hiding"):
    """Per-checkpoint values of one injury-grid condition (percent for rates, raw for survival_steps),
    or (None, None) if not yet run."""
    import window_profile as W
    O = os.path.join(EV, f"metrics_history_rppo_injurygrid_{version}")
    steps, v = W.read_series(O, label, f"{scene}_inj{inj:02d}", measure,
                             scale=1.0 if measure == "survival_steps" else 100.0)
    if steps is None:
        return None, None
    return np.asarray(steps), np.asarray(v)


def dose_grid(reading, levels, stem, kind, xlabel, note):
    """Rows: in bush / chose Rest / left the bush; columns: levels; lines: both agents (final store),
    bands: lowest-highest of the late-checkpoint stores. No predator within reach."""
    import matplotlib.pyplot as plt
    import house
    MEAS = [("bush", "in the bush (%)"), ("rest", "chose Rest (%)"), ("exit", "left the bush (%)")]
    x = np.arange(5, 100, 10)
    fig, ax = plt.subplots(len(MEAS), len(levels), figsize=(10.0, 7.6), sharex=True, sharey="row",
                           squeeze=False)
    samples = []
    for j, lv in enumerate(levels):
        for arm, alab, col in C.ARMS:
            lab = f"{lv}_{arm}"
            fin, late = dose(lab, "final"), dose(lab, "late")
            if fin is None:
                if not ax[0, j].texts:
                    ax[0, j].text(0.5, 0.5, "store not\ncollected yet", transform=ax[0, j].transAxes,
                                  ha="center", va="center", color=house.INK, fontsize=9.5)
                samples.append(dict(what=f"level {lv[-2:]} {alab}", used=0, total=1,
                                    note="final-checkpoint store not collected yet"))
                continue
            for i, (m, _) in enumerate(MEAS):
                r, _den = rate(fin[reading][m])
                ax[i, j].plot(x, r, "-o", color=col, ms=3.5, lw=1.8,
                              label=alab if (i == ax.shape[0] - 1 and j == 0) else None)
                if late:
                    L = np.array([rate(t[reading][m])[0] for t in late])
                    ax[i, j].fill_between(x, np.nanmin(L, 0), np.nanmax(L, 0), color=col, alpha=0.18, lw=0)
            den = fin[reading]["bush"][0, :, 1]
            samples.append(dict(what=f"level {lv[-2:]} {alab}: {note}",
                                used=int(den[den >= MIN_DEN].sum()), total=int(den.sum()),
                                note=f"ten-point bins under {MIN_DEN:,} decisions not drawn; bands from "
                                     f"{len(late) if late else 0} late-checkpoint stores"))
        ax[0, j].set_title(f"level {lv[-2:]}", loc="left", fontsize=10.5, color=house.INK)
    for i, (_, yl) in enumerate(MEAS):
        ax[i, 0].set_ylabel(yl)
    for j in range(len(levels)):
        ax[-1, j].set_xlabel(xlabel)
        ax[-1, j].set_xticks([0, 50, 100])
    fig.tight_layout(h_pad=1.0, w_pad=0.8)
    C.legend_below(ax[-1, 0], ncol=2, offset=-0.42)
    fig.tight_layout(h_pad=1.0, w_pad=0.8)
    C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
    C.record_kind(stem, kind)
    C.record_samples(stem, samples)
    house.save(fig, os.path.join(C.FIG, stem), column_px=C.COLUMN_PX)


# columns of every scene figure: levels 02-04 (one scene version each), 05 (four thermal versions
# pooled), 06 twice (without and with its injury-driven noise), because the noise is part of level 06
SCENE_COLS = [("lvl02", ["core"], "level 02"), ("lvl03", ["core"], "level 03"), ("lvl04", ["core"], "level 04"),
              ("lvl05", [f"{a}_clean" for a in ARMS_T], "level 05"),
              ("lvl06", [f"{a}_clean" for a in ARMS_T], "level 06\nnoise off"),
              ("lvl06", [f"{a}_noise_matched" for a in ARMS_T], "level 06\nnoise on")]


def window_mean(version, label, scene, inj, measure="bush_hiding", last=LAST):
    """(mean, sd) over the newest `last` checkpoints, and the checkpoint count, or (nan, nan, 0)."""
    s, v = scene_series(version, label, scene, inj, measure)
    if s is None:
        return np.nan, np.nan, 0
    v = v[-last:]
    return float(v.mean()), float(v.std()), len(v)


def dose_curve(versions, label, scene, measure="bush_hiding"):
    """(10,) curve over starting injury, plus lo/hi band and n versions used.

    One version: the 20-checkpoint mean, band = +-1 SD across checkpoints.
    Several versions (levels 05/06): the median over versions of their 20-checkpoint means, band =
    lowest to highest version. The caption says which is which."""
    M = np.array([[window_mean(v, label, scene, i, measure)[0] for i in INJ] for v in versions])
    if len(versions) == 1:
        sd = np.array([window_mean(versions[0], label, scene, i, measure)[1] for i in INJ])
        return M[0], M[0] - sd, M[0] + sd
    return np.nanmedian(M, 0), np.nanmin(M, 0), np.nanmax(M, 0)


def slope_series(version, label, scene, measure="bush_hiding"):
    """Per-checkpoint least-squares slope of the measure on starting injury, in points per 10 injury,
    over the ten injury levels; (steps, slopes) or (None, None). Checkpoints must match across levels."""
    S, V = None, []
    for i in INJ:
        s, v = scene_series(version, label, scene, i, measure)
        if s is None:
            return None, None
        if S is None:
            S = s
        elif not np.array_equal(S, s):
            n = min(len(S), len(s))                       # a sweep still filling in: common prefix
            if not np.array_equal(S[:n], s[:n]):
                raise ValueError(f"{version} {label} {scene}: checkpoint steps differ across injury levels")
            S, V = S[:n], [x[:n] for x in V]; v = v[:n]
        V.append(v)
    n = min(len(x) for x in V)
    Y = np.array([x[:n] for x in V])                      # (10, n)
    xs = np.array(INJ) / 10.0
    xc = xs - xs.mean()
    return S[:n], (xc[:, None] * (Y - Y.mean(0))).sum(0) / (xc ** 2).sum()


def rows_versions():
    """Every (level, version) row, in page order."""
    return [(lv, v) for lv in LEVELS for v in VERSIONS[lv]]


# ------------------------------------------------------------------ input manipulation
import pandas as pd                                                     # noqa: E402

LADDER = [round(0.1 * k, 1) for k in range(10)]
# level 06 split by whether the scene has a fire -- the contrast the scene figures point to
MANIP_COLS = [("lvl02", ["core"], "level 02"), ("lvl03", ["core"], "level 03"), ("lvl04", ["core"], "level 04"),
              ("lvl05", [f"{a}_clean" for a in ARMS_T], "level 05"),
              ("lvl06", [f"{a}_{b}" for a in ("neutral", "cool") for b in ("clean", "noise_matched")],
               "level 06\nno fire"),
              ("lvl06", [f"{a}_{b}" for a in ("fire_by_bush", "fire_away") for b in ("clean", "noise_matched")],
               "level 06\nwith fire")]


def manip_dir(version, scene_inj, label, job):
    return os.path.join(ID, "manip", version, scene_inj, label, job)


def manip_table(version, scene_inj, label, job):
    """episodes.csv of one manipulation job, or None if the job has not finished."""
    d = manip_dir(version, scene_inj, label, job)
    if not os.path.exists(os.path.join(d, "manifest.json")):
        return None
    return pd.read_csv(os.path.join(d, "episodes.csv"))


def manip_curve(versions, label, scene_inj, job, measure):
    """Per condition (identity excluded): mean over checkpoints of the per-checkpoint episode mean;
    for several versions the median over versions. Returns (values (C-1,), n_versions_used)."""
    per = []
    for v in versions:
        t = manip_table(v, scene_inj, label, job)
        if t is None:
            continue
        g = t[t.condition > 0].groupby(["condition", "checkpoint"])[measure].mean().groupby("condition").mean()
        per.append(g.to_numpy())
    if not per:
        return None, 0
    return np.median(np.array(per), 0), len(per)


# ------------------------------------------------------------------ per-step scene summaries
STEPS_DIR = os.path.join(ID, "scene_steps")
STARTS = (0, 30, 60, 90)


def steps_npz(version, label):
    p = os.path.join(STEPS_DIR, version, f"{label}.npz")
    return np.load(p) if os.path.exists(p) else None


def steps_mean(versions, label, key):
    """Mean over scene versions of one per-step array, or None."""
    arrs = [z[key] for z in (steps_npz(v, label) for v in versions) if z is not None and key in z.files]
    return (np.nanmean(np.array(arrs), 0), len(arrs)) if arrs else (None, 0)


def early_series(version, label, scene, inj):
    """Per-checkpoint share (percent) of steps 1-25 in the bush, newest 20 checkpoints, from the
    per-step summaries; (checkpoint steps, values) or (None, None)."""
    z = steps_npz(version, label)
    k = f"{scene}_inj{inj:02d}"
    if z is None or f"{k}__early_ck" not in z.files or len(z[f"{k}__early_ck"]) == 0:
        return None, None
    return z[f"{k}__checkpoints"], 100.0 * z[f"{k}__early_ck"]


def series(window, version, label, scene, inj):
    """window 'early' (steps 1-25, per-step summaries) or 'episode' (whole episode, sweep CSV)."""
    if window == "early":
        return early_series(version, label, scene, inj)
    s, v = scene_series(version, label, scene, inj)
    return (s[-LAST:], v[-LAST:]) if s is not None else (None, None)


def dose_curve_w(window, versions, label, scene):
    """As dose_curve, for either window."""
    per = []
    for v in versions:
        row = []
        for i in INJ:
            s, x = series(window, v, label, scene, i)
            row.append((np.nan, np.nan) if s is None else (x.mean(), x.std()))
        per.append(row)
    M = np.array([[m for m, _ in r] for r in per]); SD = np.array([[s for _, s in r] for r in per])
    if len(versions) == 1:
        return M[0], M[0] - SD[0], M[0] + SD[0]
    return np.nanmedian(M, 0), np.nanmin(M, 0), np.nanmax(M, 0)


def slopes_w(window, version, label, scene):
    """Per-checkpoint least-squares slope over the ten starting injuries (points per 10 injury)."""
    S, V = None, []
    for i in INJ:
        s, v = series(window, version, label, scene, i)
        if s is None:
            return None
        if S is None:
            S = s
        n = min(len(S), len(s))
        if not np.array_equal(S[:n], s[:n]):
            raise ValueError(f"{version} {label} {scene}: checkpoints differ across injury levels")
        V.append(v)
    n = min(len(x) for x in V)
    Y = np.array([x[:n] for x in V]); xs = np.array(INJ) / 10.0; xc = xs - xs.mean()
    return (xc[:, None] * (Y - Y.mean(0))).sum(0) / (xc ** 2).sum()

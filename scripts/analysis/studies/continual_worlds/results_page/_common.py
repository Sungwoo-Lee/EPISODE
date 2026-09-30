"""Shared paths, data loaders and helpers for the 'Continual Worlds: Results' page
(docs/experiments/active/continual_worlds/continual_worlds_results.html).

The page reports TWO studies:
  * the main continual-worlds sequences (CONTINUAL_WORLDS.md sections 10-11): three A-B-A-B sequences,
    one ordinary and one modulated run each, all branching from one pair of pre-trained checkpoints;
  * the May double-return replication (MAY_DOUBLE_RETURN_REPLICATION.md sections 10-11): three seeds
    per agent, trained from scratch on May's five-stage schedule.

Same house pattern as the planning page (../page/_common.py): record_kind, record_samples, save with
the text guards and the phone-floor check. NEW here: record_numbers(stem, {...}) -- every number the
page's PROSE quotes is emitted by the script that computed it into figures/<stem>.nums.json and
substituted by the builder as __N:<stem>.<key>__, so no number on the page is typed by hand.

Data sources, all READ, never re-derived where an analysis output already holds the value:
  results/analysis/continual_worlds/pilot_readout.json            main runs, per-stage levels, per-switch readings
  results/analysis/continual_worlds/forgetting_{p1,p2,p3}_{t1none,t16quad}.json   frozen-checkpoint matrices
  results/analysis/continual_worlds/sampled_check_p3.json         sampled-action re-check of key cells
  results/analysis/continual_worlds/mayrep_readout.json           May replication read-out
  results/analysis/continual_worlds/retention_mayrep_readout.json frozen-agent retention test
  tmp/20260929_cw_main_verdict.json      the analyzer's per-switch noise yardstick, return and forgetting
                                         votes and the R1-R6 sensitivity table (not in the read-out JSON)
  tmp/20260930_cw_sensitivity_extra.json R7 / R8 rows added after the verdict review
  tmp/20260930_cw_zeroshot_relative.json head-start vs gain on first visits (exploratory)
  tmp/20260930_cw_shared_start_l05.json  the bitwise shared-start check of the main study's pre-trained pair
  local WandB binaries (wandb/run-*-<id>/run-<id>.wandb) for the training CURVES only, read through the
  read-out script's own scan() / Series, so curves and read-out numbers share one code path.
The four tmp/ files are the analyzer's working outputs (gitignored); the page's Reproduce section says so.

This folder sits FOUR levels below the repo root, so ROOT walks five '..'.

Colour: blue = ordinary agent, orange = modulated agent (the convention of the sibling page "What Both
Agents Compute"); ink = a modulated-minus-ordinary difference; grey = noise yardsticks and context.
The chrome accent is moved off both hues in the template (F11 amendment).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "studies", "continual_worlds"))
import house                                                          # noqa: E402
from figguards import (assert_min_text_px, assert_no_text_overlap,   # noqa: E402,F401
                       assert_ticks_dont_collide, COLUMN_PX)

FIG = os.path.join(ROOT, "docs/experiments/active/continual_worlds/figures")
RA = os.path.join(ROOT, "results/analysis/continual_worlds")
READOUT = os.path.join(RA, "pilot_readout.json")
MAYREP = os.path.join(RA, "mayrep_readout.json")
RETENTION = os.path.join(RA, "retention_mayrep_readout.json")
SAMPLED = os.path.join(RA, "sampled_check_p3.json")
VERDICT = os.path.join(ROOT, "tmp/20260929_cw_main_verdict.json")
SENS_EXTRA = os.path.join(ROOT, "tmp/20260930_cw_sensitivity_extra.json")
ZEROSHOT = os.path.join(ROOT, "tmp/20260930_cw_zeroshot_relative.json")
SHARED = os.path.join(ROOT, "tmp/20260930_cw_shared_start_l05.json")   # bitwise shared-start check, main-study pair
CACHE = os.path.join(ROOT, "tmp/cw_results_page_cache")      # scratch; keyed by the .wandb file's size + mtime

KIND = {"training": "training logs — survival while learning, sampled actions",
        "evaluation": "frozen checkpoints — no training, 2,000 test episodes per cell",
        "mixed": "training logs and frozen-checkpoint tests side by side",
        "exploratory": "exploratory — a measure chosen after the data were seen"}

ORD, MOD = house.BLUE, house.ORANGE          # agent colours (sibling page convention)
AGENT_LABEL = {"ordinary": "ordinary agent", "modulated": "modulated agent"}
AGENT_COL = {"ordinary": ORD, "modulated": MOD}
# Seed markers: shapes no other encoding on the page uses (circle = sampled actions, square = most-likely
# action, triangle = first 20k, diamond = means) -- format register F11 third amendment.
SEED_MARKER = {42: "h", 43: "X", 44: "P"}
GREY = "#8a8f99"
BAND = "#e4e6e3"                             # a noise band's fill
SMALLEST_PT = 9.5                            # every hand-set text size; ticks are 11 pt
FLOOR_PX = 685                               # the page's .figscroll min-width; see save()

# Display names: the planning page's names for the worlds (project vocabulary, not invented).
WORLD = {"forage": "Forage", "winter": "Winter", "famine": "Famine", "danger_scout_a": "Danger-A",
         "fog_scout_b": "Fog-B", "home": "Home", "nursery": "Nursery"}
# The three main sequences: tag family in the read-out -> (short name, the two alternating worlds)
SEQ = {"P1": ("rppo_cw_p1_danger_scout_a_famine_s42", "Danger-A ↔ Famine"),
       "P2": ("rppo_cw_p2_fog_scout_b_danger_scout_a_s42", "Fog-B ↔ Danger-A"),
       "P3": ("rppo_cw_p3_s42", "Winter ↔ Famine")}
FORGET_FILE = {"P1": "p1", "P2": "p2", "P3": "p3"}
AGENT_FILE = {"ordinary": "t1none", "modulated": "t16quad"}


def load(path):
    if not os.path.exists(path):
        raise SystemExit(f"missing input {os.path.relpath(path, ROOT)} - rerun the analysis that writes it")
    return json.load(open(path))


# ---------------------------------------------------------------- main-study accessors -------
def main_pairs():
    """{P1: {'pair': common_reference entry, 'ordinary': run, 'modulated': run}, ...} from the read-out."""
    RO = load(READOUT)
    runs = {str(r["run"]): r for r in RO["runs"]}
    cr = {c["pair"]: c for c in RO["common_reference"]}
    out = {}
    for s, (pair, _) in SEQ.items():
        c = cr[pair]
        assert c["role"] == "vote", (pair, c["role"])
        out[s] = {"pair": c, "ordinary": runs[c["runs"]["ordinary"]], "modulated": runs[c["runs"]["modulated"]]}
        for a in ("ordinary", "modulated"):
            assert out[s][a]["finished"], (s, a)
    return out


def forgetting(seq, agent):
    return load(os.path.join(RA, f"forgetting_{FORGET_FILE[seq]}_{AGENT_FILE[agent]}.json"))


def row_label(label):
    """'end_02_danger_scout_a' -> 'end of stage 2 (Danger-A)'; 'start' -> 'branch point'."""
    if label == "start":
        return "branch point (before any switch)"
    _, k, w = label.split("_", 2)
    return f"end of stage {int(k)} ({WORLD[w]})"


# ---------------------------------------------------------------- training curves ------------
KEEP = ("Episode/Number", "Episode/Steps", "Episode/_window_n", "Episode/Term_MaxSteps", "stage/index")


def rows(wandb_dir):
    """Episode rows of one run, read by the read-out's own scan() and cached (only the keys the page
    uses; reward is never kept). The cache is invalidated when the .wandb file changes."""
    import glob
    import pilot_readout as pr
    wd = os.path.join(ROOT, wandb_dir) if not os.path.isabs(wandb_dir) else wandb_dir
    f = glob.glob(os.path.join(wd, "run-*.wandb"))
    assert len(f) == 1, wd
    st = os.stat(f[0])
    key = f"{os.path.basename(wd)}_{st.st_size}_{int(st.st_mtime)}.json"
    os.makedirs(CACHE, exist_ok=True)
    cp = os.path.join(CACHE, key)
    if os.path.exists(cp):
        return json.load(open(cp))
    rr, _ = pr.scan(wd)
    out = [{k: r[k] for k in KEEP if k in r} for r in rr]
    json.dump(out, open(cp, "w"))
    return out


def stage_series(run, k, allrows=None):
    """pilot_readout.Series for stage k (0-based) of a sequence run, split exactly as the read-out
    splits it (rows in (from, to + 4000] carrying stage/index == k)."""
    import pilot_readout as pr
    rr = allrows if allrows is not None else rows(run["wandb_dir"])
    st = run["stages"][k]
    assert st["stage"] == k, (run["tag"], k)
    lo, hi = st["from"], st["to"]
    srows = [r for r in rr if lo < r["Episode/Number"] <= hi + 4000 and int(r.get("stage/index", -1)) == k]
    return pr.Series(srows, lo)


def running(ser, window=20_000, key="Episode/Steps"):
    """(episodes since the stage start, trailing `window`-episode mean) at every row with a full window,
    using the read-out's episode weighting."""
    import numpy as np
    xs, ys = [], []
    for e in ser.e:
        if e - ser.start >= window:
            v = ser.mean(key, e - window, e)
            if v is not None:
                xs.append(e - ser.start); ys.append(v)
    return np.array(xs), np.array(ys)


# ---------------------------------------------------------------- page plumbing --------------
def record_samples(stem, rows_):
    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(FIG, f"{stem}.data.txt"), "w") as fh:
        for r in rows_:
            assert "|" not in r["what"] + r["note"], f"'|' is the field separator: {r}"
            # F69 amendment: no bare paths or identifiers in a data-statement cell
            assert "/" not in r["note"] and "_" not in r["note"] + r["what"], f"path/identifier in data note: {r}"
            pct = 100.0 * r["used"] / r["total"] if r["total"] else 0.0
            u = f"{r['used']:,}" if isinstance(r["used"], int) else r["used"]
            t = f"{r['total']:,}" if isinstance(r["total"], int) else r["total"]
            fh.write(f"{r['what']}|{u}|{t}|{pct:.1f}|{r['note']}\n")
    print(f"  wrote {stem}.data.txt ({len(rows_)} rows)")


def record_kind(stem, kind):
    assert kind in KIND, kind
    os.makedirs(FIG, exist_ok=True)
    open(os.path.join(FIG, f"{stem}.kind.txt"), "w").write(kind + "\n")


def record_numbers(stem, nums):
    """Every number the page prose quotes, pre-formatted as the page prints it (strings)."""
    for k, v in nums.items():
        assert isinstance(v, str), f"{stem}.{k}: format numbers as strings in the script ({v!r})"
    os.makedirs(FIG, exist_ok=True)
    json.dump(nums, open(os.path.join(FIG, f"{stem}.nums.json"), "w"), indent=1, ensure_ascii=False)
    print(f"  wrote {stem}.nums.json ({len(nums)} numbers)")


def fmt(x, nd=1, sign=False):
    """Format a number the way the page prints it: a true minus sign, optional explicit plus."""
    s = f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"
    return s.replace("-", "−")


def save(fig, stem, check_text=True):
    """Guards, then house.save, then the phone-floor check on the SAVED raster (as ../page/_common.save:
    9.5 pt at 220 dpi is 29.0 px, so the PNG must be at most 2209 px wide for 9 px text at the page's
    685 px .figscroll floor)."""
    assert_no_text_overlap(fig)
    assert_min_text_px(fig)
    dpi = fig.dpi
    house.save(fig, os.path.join(FIG, stem), column_px=COLUMN_PX, check_text=check_text)
    from PIL import Image
    w = Image.open(os.path.join(FIG, f"{stem}.png")).size[0]
    need = w * 9.0 / (SMALLEST_PT * dpi / 72.0)
    if need > FLOOR_PX:
        raise SystemExit(f"{stem}: canvas {w}px needs a {need:.0f}px phone floor for 9px text, "
                         f"above the page's {FLOOR_PX}px; narrow the figure")
    print(f"  {stem}: canvas {w}px, phone floor needed {need:.0f}px (page gives {FLOOR_PX}px)")

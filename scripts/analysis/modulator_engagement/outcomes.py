"""Behaviour outcomes per pair, read through the replication page's own code at a pinned commit.

Plain-language purpose: the engagement check correlates a modulator measure with the behaviour
gaps the fast-bush-healing replication page reported. Those gaps must be the page's numbers, not a
re-derivation, so they are computed by the page's own `figures.py` -- and by the version committed
at `10358a45`, because another session has uncommitted edits in the working copy.

How the pinning works. `figures.py` imports `highlight.py` (and through it `collect.py`,
`checkpoint_stats.py`, the Basic Behaviour estimator) by paths relative to itself, so extracting
the one file would mix pinned and current code. This module extracts the whole `scripts/` tree of
the pinned commit with `git archive` into a gitignored directory, checks every extracted file of the
import chain against the commit's blob hashes, and runs the reader in a subprocess whose import
path holds ONLY that tree. The data root (`collect.ROOT`, which would otherwise point inside the
extracted tree, where `results/` does not exist) is redirected to this repository; that changes
where CSVs are read from, never how they are combined. (`git archive` rather than `git worktree`:
same pinned files, and no write to `.git`, which parallel sessions share.)

The 9 main pairs and the two 22-Sep originals are read from the pinned tree. The level-05
fixed-start pairs do not exist at that commit; they are read through the WORKING COPY and labelled
so. The 9 main pairs are read through the working copy too, and must match the pinned numbers
exactly (fatal otherwise).

Per pair and agent: `inj` (no animal, injured 70 minus unhurt 0), `injw` (wandering rabbit, 70 - 0),
`pred` (hunting predator minus no animal, unhurt), and `base` (no animal, unhurt bush dwell itself),
each the mean over the 0.2 M checkpoint grid from 2 to 10 M steps, in percentage points of bush
dwell, with the grid points used. Optional own-scene variants feed the level-05 sensitivity row.

    python scripts/analysis/modulator_engagement/outcomes.py --out results/analysis/modulator_engagement/outcomes.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PINNED_SHA = "10358a45"
FIG_REL = "scripts/analysis/studies/fast_heal_replication/figures.py"
CHAIN = (FIG_REL, "scripts/analysis/studies/f7b_across_runs/highlight.py",
         "scripts/analysis/studies/f7b_across_runs/collect.py",
         "scripts/analysis/studies/f7b_across_runs/checkpoint_stats.py")
GRID_LO_M, GRID_STEP_M = 2.0, 0.2

# Runs in a subprocess with sys.path = [<code root>/scripts/analysis/studies/fast_heal_replication].
_READER = r'''
import json, os, sys
code_root, data_root, req = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
sys.path.insert(0, os.path.join(code_root, "scripts/analysis/studies/fast_heal_replication"))
import figures as F
HL, K, C = F.HL, F.K, F.C
C.ROOT = data_root                       # read results/ from the live repo; code stays pinned
assert os.path.abspath(F.__file__).startswith(os.path.abspath(code_root)), F.__file__
assert os.path.abspath(HL.__file__).startswith(os.path.abspath(code_root)), HL.__file__

def prof(v):
    p = C.P.W.window_profile(v.to_numpy(), windows=[len(v)]).iloc[0]
    return {"mean": float(p["mean"]), "lo": float(p["lo"]), "hi": float(p["hi"]), "n": int(len(v)),
            "steps": [int(s) for s in v.index]}

def measures(leaf):
    out = {}
    for m, ab, _ in F.MEASURES:
        e = F.effect(leaf, *ab)
        if e is None:
            out[m] = None
            continue
        va, vb = HL.series(leaf, *ab[0]), HL.series(leaf, *ab[1])
        v = K.on_grid((va - vb).dropna(), HL.LO_M, HL.HI_M, HL.SPACING_M)
        d = prof(v)
        if abs(d["mean"] - e[0]) > 0 or d["n"] != e[3]:
            raise AssertionError(f"{leaf} {m}: step reconstruction disagrees with figures.effect")
        out[m] = d
    b = HL.series(leaf, "none", "00")
    out["base"] = None if b is None else prof(K.on_grid(b.dropna(), HL.LO_M, HL.HI_M, HL.SPACING_M))
    return out

res = {}
for key, how, lv, seed, scene_set in req:
    if how == "reference":
        leaves = {a: F.REFERENCE[lv][a] for a in ("ordinary", "modulated")}
    else:
        ss = F.MAIN_SET[lv] if scene_set == "main" else scene_set
        leaves = {a: F.leaf(lv, ss, a, seed) for a in ("ordinary", "modulated")}
    res[key] = {"leaf": leaves, **{a: measures(l) for a, l in leaves.items()}}
print("@@JSON@@" + json.dumps(res))
'''


def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], check=True, capture_output=True, text=True).stdout.strip()


def extract_pinned(dest):
    """`git archive <sha> scripts` into dest (idempotent), then verify the import chain's blobs."""
    full = _git("rev-parse", PINNED_SHA)
    mark = os.path.join(dest, ".pinned_sha")
    if not (os.path.exists(mark) and open(mark).read().strip() == full):
        os.makedirs(dest, exist_ok=True)
        tar = subprocess.run(["git", "-C", ROOT, "archive", full, "scripts"], check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", dest], input=tar, check=True)
        open(mark, "w").write(full + "\n")
    blobs = {}
    for rel in CHAIN:
        want = _git("rev-parse", f"{full}:{rel}")
        data = open(os.path.join(dest, rel), "rb").read()
        got = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        if got != want:
            raise RuntimeError(f"pinned tree {dest}: {rel} blob {got} != commit's {want}")
        blobs[rel] = want
    return full, blobs


def _run_reader(code_root, req):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    p = subprocess.run([sys.executable, "-c", _READER, code_root, ROOT, json.dumps(req)],
                       capture_output=True, text=True, cwd=code_root, env=env)
    if p.returncode:
        raise RuntimeError(f"outcome reader failed under {code_root}:\n{p.stderr[-3000:]}")
    line = [x for x in p.stdout.splitlines() if x.startswith("@@JSON@@")][-1]
    return json.loads(line[len("@@JSON@@"):])


def _req(pairs, scene_set="main"):
    out = []
    for p in pairs:
        if p.group == "oos_orig":
            # figures.REFERENCE is keyed by the page's level names: lvl04 -> l04, lvl05 -> l05
            out.append([p.key, "reference", "l" + p.level[-2:], p.seed, scene_set])
        else:
            out.append([p.key, "leaf", p.level, p.seed, scene_set])
    return out


def gaps(rec):
    """Per-pair derived outcomes from one reader record: modulated minus ordinary, plus own effects."""
    o, m = rec["ordinary"], rec["modulated"]
    g = {}
    for k in ("inj", "injw", "pred", "base"):
        g[f"gap_{k}"] = (m[k]["mean"] - o[k]["mean"]) if (m.get(k) and o.get(k)) else None
        g[f"mod_{k}"] = m[k]["mean"] if m.get(k) else None
        g[f"ord_{k}"] = o[k]["mean"] if o.get(k) else None
    # the pair's own checkpoint set of the primary outcome (both agents), as grid indices
    # g = 0..40 for 2.0 + 0.2 g M steps -- the same numbering as engagement.grid_index_map
    gi = lambda d: {int(round((s / 1e6 - GRID_LO_M) / GRID_STEP_M)) for s in d["steps"]}
    g["grid_points"] = sorted(gi(m["injw"]) & gi(o["injw"])) if (m.get("injw") and o.get("injw")) else []
    return g


def read_all(pinned_dir):
    from scripts.analysis.modulator_engagement import runs as R
    pinned_dir = os.path.abspath(pinned_dir)
    full, blobs = extract_pinned(pinned_dir)
    main = [p for p in R.PAIRS if p.group == "main"]
    orig = [p for p in R.PAIRS if p.group == "oos_orig"]
    fix = [p for p in R.PAIRS if p.group == "oos_fix"]
    own = [p for p in R.PAIRS if p.group == "main" and p.own_spec]

    pinned = _run_reader(pinned_dir, _req(main + orig))
    pinned_own = _run_reader(pinned_dir, [[k + "__own", h, lv, s, "own"] for k, h, lv, s, _ in _req(own)])
    work = _run_reader(ROOT, _req(main + fix))

    for p in main:                       # the working copy must reproduce the pinned numbers exactly
        if pinned[p.key] != work[p.key]:
            raise AssertionError(f"{p.key}: working-copy outcomes differ from the pinned {PINNED_SHA} ones")
    for p in main + fix + orig:          # the leaf read must be the spec's own output for these labels
        _probe, _ep, out_dir, labels = R.spec_scene(p)
        rec = pinned.get(p.key) or work[p.key]
        for a, lab in labels.items():
            if os.path.normpath(rec["leaf"][a]) != os.path.normpath(os.path.join(out_dir, lab)):
                raise AssertionError(f"{p.key}/{a}: outcome leaf {rec['leaf'][a]} is not "
                                     f"{out_dir}/{lab} from {p.spec}")

    out = {}
    for p in main + orig:
        out[p.key] = {"source": f"pinned {full[:8]}", **pinned[p.key], **gaps(pinned[p.key])}
    for p in fix:
        out[p.key] = {"source": "working copy (l05fix is not in the pinned commit)", **work[p.key],
                      **gaps(work[p.key])}
    for k, rec in pinned_own.items():         # own-scene sensitivity rows (levels 05 and 06)
        out[k] = {"source": f"pinned {full[:8]}", **rec, **gaps(rec)}
    prov = {"pinned_sha": full, "pinned_tree": os.path.abspath(pinned_dir), "blobs": blobs,
            "working_copy_figures_dirty": bool(_git("status", "--porcelain", FIG_REL)),
            "head": _git("rev-parse", "HEAD"),
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "main_pinned_equals_working": True}
    return out, prov


def main(argv=None):
    sys.path.insert(0, ROOT)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="outcomes JSON to write")
    ap.add_argument("--pinned-dir", required=True,
                    help="where to extract the pinned scripts/ tree (gitignored, e.g. under results/analysis/)")
    a = ap.parse_args(argv)
    out, prov = read_all(a.pinned_dir)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"provenance": prov, "pairs": out}, open(a.out, "w"), indent=1)
    print(f"wrote {len(out)} outcome records to {a.out}")


if __name__ == "__main__":
    main()

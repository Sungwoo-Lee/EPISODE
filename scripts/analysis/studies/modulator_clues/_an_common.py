"""_an_common.py - what the six `an0N_*` figures of "What Both Agents Compute" share.

WHAT THIS IS. Reading, policy and data-statement code for the figures that
`build_algorithmic_null_page.py` embeds. Each figure script reads ONE analysis-driver output
(`run_similarity`, `run_decoding`, `run_wakeup`, `run_activations`) and draws it. Plan:
docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, File Changes 9 and 10.

FOUR RULES THIS MODULE ENFORCES.
  1. A figure never recomputes a statistic. It reads the numbers the driver wrote; the only
     arithmetic here is presentation (a percentage of two counts the driver wrote, an axis range).
  2. A verdict word reaches a figure only through `verdict()`: the string must come from the
     output's own evaluation block, the output's policy must allow verdict words, and when the
     policy has a prefix ("provisional - end of stage 1 of 5") the word must carry it. For the pilot
     the policy forbids words, so `verdict()` raises and the figure writes the rules' "no verdict is
     drawn" instead.
  3. Every figure carries the output's rules sha, evidence status and label, both drawn on the
     image (`footer`) and in its `<stem>.data.txt` (`write_data`). An output stamped with an earlier
     rules sha is drawn only if the CURRENT rules file names that sha as a revision's
     `sha256_before` (the rules' revision entry says the earlier verdict "is reported with that sha");
     the figure then says so.
  4. A figure drawn from an input that is not a registered driver output (a synthetic file, or a
     partial summary written to tmp/) is labelled TEST INPUT on the image and in its data statement,
     and is refused the page's own figure folder, so it cannot be embedded by accident.

THE DATA STATEMENT FORMAT (`<stem>.data.txt`, one item per line; the builder parses it):
    status: <evidence status, label, verdict prefix and the policy's verdict statement>
    decision_rules: <rules file> <sha256> @ <commit>
    source: <driver output read> (generated <utc>, <driver>)
    row: <what>|<used>|<available>|<percent>|<why>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import textwrap

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house                                           # noqa: E402
from figguards import assert_min_text_px, assert_no_text_overlap   # noqa: E402,F401

#: The page's own figure folder. Nothing here reads, lists or writes its parent `figures/`, which
#: holds another page's figures (tooling plan, finding 7).
FIG_DIR = os.path.join(ROOT, "docs/experiments/active/modulator_clues/figures/algorithmic_null")
RESULTS = os.path.join(ROOT, "results/analysis/algorithmic_null")
RULES = "docs/experiments/active/modulator_clues/algorithmic_null_decision_rules.yaml"
#: Registered driver outputs are written under RESULTS by a manifest committed under MANIFESTS.
MANIFESTS = "docs/experiments/active/modulator_clues/"
COLUMN_PX = 688                                        # this page's text column (figguards default)

ORD, MOD, UNTR = house.BLUE, house.ORANGE, house.TEXT_LIGHT   # ordinary / modulated / untrained
ARM_NAME = {"ordinary": "ordinary agent", "modulated": "modulated agent"}


# ------------------------------------------------------------------------------ CLI ---------
def cli(doc: str, default_source: str, extra=()) -> argparse.Namespace:
    """`extra`: (flag, argparse kwargs) pairs a script adds to the shared --source / --out."""
    ap = argparse.ArgumentParser(description=doc.strip().splitlines()[0])
    for flag, kw in extra:
        ap.add_argument(flag, **kw)
    ap.add_argument("--source", default=default_source,
                    help=f"driver output to draw (default: {os.path.relpath(default_source, ROOT)})")
    ap.add_argument("--out", default=FIG_DIR,
                    help="folder to write <stem>.{png,svg,pdf,data.txt} into (default: the page's "
                         "own figure folder; a TEST INPUT is refused there)")
    return ap.parse_args()


def rel(path: str) -> str:
    return os.path.relpath(os.path.abspath(path), ROOT)


# ------------------------------------------------------------------------------ reading -----
def load(path: str, policy_from_rules: bool = False) -> dict:
    """A driver output. `policy_from_rules`: the output (run_wakeup's b2_reading.json) stamps its
    evidence status but not the policy fields; take them from the rules file at the output's OWN
    sha, never from the current one."""
    if not os.path.exists(path):
        raise SystemExit(f"no driver output at {rel(path)} - run its driver first")
    with open(path) as fh:
        doc = json.load(fh)
    if policy_from_rules and "verdict_statement" not in doc:
        pol = rules_at(doc["decision_rules"]["sha256"])["evidence_status"].get(doc["evidence_status"])
        if pol is None:
            raise SystemExit(f"{rel(path)}: the rules define no evidence status {doc['evidence_status']!r}")
        doc["verdict_words_allowed"] = bool(pol["verdict_words_allowed"])
        doc["verdict_prefix"] = pol.get("verdict_prefix")
        doc.setdefault("label", pol.get("label"))
        doc["verdict_statement"] = ("verdict words come only from decision_rules.evaluate_*"
                                    if doc["verdict_words_allowed"] else "no verdict is drawn")
    for k in ("decision_rules", "evidence_status", "verdict_statement"):
        if k not in doc:
            raise SystemExit(f"{rel(path)}: not a driver output (no '{k}' stamp)")
    for k in ("file", "sha256"):
        if k not in doc["decision_rules"]:
            raise SystemExit(f"{rel(path)}: decision_rules stamp has no '{k}'")
    return doc


def is_test_input(path: str, doc: dict) -> bool:
    """True unless the file sits under results/analysis/algorithmic_null/ AND was written for a
    manifest committed under the modulator_clues docs folder."""
    under = os.path.abspath(path).startswith(RESULTS + os.sep)
    man = str(doc.get("manifest") or "")
    return not (under and man.startswith(MANIFESTS))


def check_out(out: str, test: bool) -> str:
    out = os.path.abspath(out)
    if test and (out == FIG_DIR or out.startswith(FIG_DIR + os.sep)
                 or out.startswith(os.path.join(ROOT, "docs") + os.sep)):
        raise SystemExit("a TEST INPUT figure may not be written under docs/ (it could be embedded "
                         "in the page by accident); pass --out tmp/<folder>")
    os.makedirs(out, exist_ok=True)
    return out


# ------------------------------------------------------------------------------ rules -------
def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def current_rules() -> tuple[str, dict]:
    with open(os.path.join(ROOT, RULES), "rb") as fh:
        b = fh.read()
    return _sha(b), yaml.safe_load(b)["decision_rules"]


_OLD: dict = {}


def rules_at(sha: str) -> dict:
    """The rules file whose whole-file sha256 is `sha`: the working copy, or a committed version
    found in the file's git history by its sha256. Raises if neither matches."""
    cur_sha, cur = current_rules()
    if sha == cur_sha:
        return cur
    if sha not in _OLD:
        commits = subprocess.run(["git", "-C", ROOT, "log", "--format=%H", "--", RULES],
                                 capture_output=True, text=True, timeout=120).stdout.split()
        for c in commits:
            b = subprocess.run(["git", "-C", ROOT, "show", f"{c}:{RULES}"],
                               capture_output=True, timeout=120).stdout
            if _sha(b) == sha:
                _OLD[sha] = yaml.safe_load(b)["decision_rules"]
                break
        else:
            raise SystemExit(f"no version of {RULES} in git has sha256 {sha[:12]}")
    return _OLD[sha]


def rules_note(doc: dict) -> str:
    """'' when the output was computed under the current rules; otherwise a sentence naming the
    revision that registered its sha as `sha256_before`. Any other sha is refused."""
    sha = doc["decision_rules"]["sha256"]
    cur_sha, cur = current_rules()
    if sha == cur_sha:
        return ""
    for rv in cur.get("revisions", []):
        if rv.get("sha256_before") == sha:
            ids = ", ".join(c.get("id", "?") for c in rv.get("changes", []))
            return (f"computed under the rules before the {rv.get('date', '')} revision "
                    f"({ids}); reported with that sha, as the revision requires. The current rules "
                    f"file is {cur_sha[:12]}.")
    raise SystemExit(f"output stamped with rules sha {sha[:12]}, which is neither the current "
                     f"rules file ({cur_sha[:12]}) nor a registered revision's sha256_before")


def param(rules: dict, dotted: str):
    node = rules["parameters"]
    for k in dotted.split("."):
        if not isinstance(node, dict) or k not in node:
            raise SystemExit(f"rules parameters have no '{dotted}'")
        node = node[k]
    return node


# ------------------------------------------------------------------------------ policy ------
def status_text(doc: dict) -> str:
    s = doc["evidence_status"]
    if doc.get("label"):
        s += f' — "{doc["label"]}"'
    if doc.get("verdict_prefix"):
        s += f' — every verdict word carries the prefix "{doc["verdict_prefix"]}"'
    return s + f"; {doc['verdict_statement']}"


def allowed(doc: dict) -> bool:
    return bool(doc.get("verdict_words_allowed"))


def verdict(doc: dict, word, test: bool = False) -> str:
    """The ONLY way a verdict word reaches a figure. `word` must be a string the driver's
    evaluator wrote. Refused when the policy forbids words; refused without the policy's prefix;
    and a TEST INPUT never shows one (its reading is not the registered reading)."""
    if not allowed(doc):
        raise SystemExit(f"evidence status {doc['evidence_status']!r} allows no verdict word")
    if test:
        return "test input — no reading shown"
    if not isinstance(word, str) or not word:
        raise SystemExit(f"verdict word {word!r} is not an evaluator string")
    pre = doc.get("verdict_prefix")
    if pre and not word.startswith(pre):
        raise SystemExit(f"verdict word {word!r} lacks the policy prefix {pre!r}")
    return word


def strip_prefix(doc: dict, word: str) -> str:
    """For a figure that states the prefix ONCE (in its footer) and the words after it. The word
    has already passed `verdict()`, so the prefix is known to be there."""
    pre = doc.get("verdict_prefix")
    return word[len(pre):].lstrip(" :") if pre and word.startswith(pre) else word


# ------------------------------------------------------------------------------ drawing -----
def blank(ax):
    """A text-only panel. Not `axis("off")`: that hides the tick labels without making them
    invisible, and the text-overlap guard then sees them under the text."""
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_facecolor(house.PAPER)
    return ax


def wrap(s: str, width: int) -> str:
    return "\n".join(textwrap.wrap(s, width=width, break_on_hyphens=False))


def footer(fig, doc: dict, test: bool, extra: str = "", width: int = 150, y: float = 0.0):
    """Rules sha, evidence status and label, drawn on the image itself (bottom left)."""
    dr = doc["decision_rules"]
    lines = []
    if test:
        lines.append("TEST INPUT — not a registered driver output; not for the page")
    lines.append(f"evidence status: {status_text(doc)}")
    note = rules_note(doc)
    lines.append(f"decision rules sha256 {dr['sha256'][:12]} @ "
                 f"{str(dr['commit'])[:8] if dr.get('commit') else 'uncommitted'}"
                 + (f" — {note}" if note else ""))
    if extra:
        lines.append(extra)
    txt = "\n".join(wrap(l, width) for l in lines)
    fig.text(0.01, y, txt, ha="left", va="top", fontsize=house.FS_LABEL, color=house.INK_2,
             linespacing=1.35)


def finish(fig, stem: str, out: str):
    assert_no_text_overlap(fig)
    assert_min_text_px(fig, column_px=COLUMN_PX)
    house.save(fig, os.path.join(out, stem), column_px=COLUMN_PX)


def pct(used, total) -> str:
    return f"{100.0 * used / total:.1f}" if total else "n/a"


def write_data(stem: str, out: str, doc: dict, source: str, test: bool, rows: list[dict]):
    """<stem>.data.txt: status, rules line, source, and used / available / % rows (guide 11b).
    Every count comes from the driver output; nothing is typed."""
    if not rows:
        raise SystemExit(f"{stem}: a figure must declare how much data it used (guide 11b)")
    dr = doc["decision_rules"]
    note = rules_note(doc)
    st = ("TEST INPUT (not a registered driver output) — " if test else "") + status_text(doc)
    lines = [f"status: {st}" + (f" Rules note: {note}" if note else ""),
             f"decision_rules: {dr['file']} {dr['sha256']} @ {dr.get('commit') or 'uncommitted'}",
             f"source: {rel(source)} (generated {doc.get('generated_utc', '?')}, "
             f"{doc.get('driver', doc.get('measure', '?'))})"]
    for r in rows:
        for k in ("what", "used", "total", "note"):
            if k not in r:
                raise SystemExit(f"{stem}: data row lacks '{k}': {r}")
        cells = [str(r["what"]), f"{r['used']:,}" if isinstance(r["used"], int) else str(r["used"]),
                 f"{r['total']:,}" if isinstance(r["total"], int) else str(r["total"]),
                 pct(r["used"], r["total"]) if isinstance(r["used"], (int, float))
                 and isinstance(r["total"], (int, float)) else "n/a", str(r["note"])]
        if any("|" in c or "\n" in c for c in cells):
            raise SystemExit(f"{stem}: a data cell holds '|' or a newline: {cells}")
        lines.append("row: " + "|".join(cells))
    with open(os.path.join(out, f"{stem}.data.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"  wrote {rel(os.path.join(out, stem + '.data.txt'))} ({len(rows)} rows)")

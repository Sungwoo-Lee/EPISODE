"""Load the pre-registered decision-rules file an analysis manifest pins, and read its numbers.

Plain-language purpose: every analysis manifest of "What Both Agents Compute" names the rules
file (`decision_rules: {file, sha256}`) and the sha256 of its whole content. This module
hashes the file, refuses to go on if the hash differs, and hands back the rules' `parameters:`
block, so that no threshold is ever typed into a script. It also returns what each evidence
status may say (`evidence_status.<status>`): for the pilot, no verdict word at all.

It is the load/pin half of the plan's `decision_rules.load` (File Changes §6). It exists now
because the Stage 2 replay needs gate G1/G2/G3/G6 numbers before the Stage 3 evaluator
(`decision_rules.py`) is written; that module is to import `load` from here rather than
re-implement it. Nothing here evaluates a rule.

Plan: docs/develop/active/neuromodulation/ALGORITHMIC_NULL_ANALYSIS_TOOLING.md, §E.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass

import yaml

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


@dataclass
class PinnedRules:
    path: str            # repo-relative path as the manifest names it
    sha256: str          # whole-file sha256, checked equal to the manifest's pin
    commit: str | None   # last commit touching the file (None if never committed)
    dirty: bool          # the file has uncommitted changes
    rules: dict          # the `decision_rules` mapping
    parameters: dict     # rules['parameters']


def _abs(p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(_ROOT, p)


def load(manifest: dict) -> PinnedRules:
    """Hash the pinned file and compare with the manifest; mismatch raises ValueError."""
    if "decision_rules" not in manifest or not isinstance(manifest["decision_rules"], dict):
        raise ValueError("manifest: mandatory key 'decision_rules: {file, sha256}' is missing")
    pin = manifest["decision_rules"]
    for k in ("file", "sha256"):
        if k not in pin or pin[k] in (None, ""):
            raise ValueError(f"manifest: decision_rules.{k} is missing")
    path = _abs(pin["file"])
    with open(path, "rb") as f:
        raw = f.read()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != pin["sha256"]:
        raise ValueError(
            f"decision rules {pin['file']}: sha256 {sha} differs from the manifest's pin "
            f"{pin['sha256']}. The rules changed after the manifest was pinned; the designer "
            f"re-pins, the tooling never does.")
    doc = yaml.safe_load(raw)
    if "decision_rules" not in doc or "parameters" not in doc["decision_rules"]:
        raise ValueError(f"{pin['file']}: no decision_rules.parameters block")
    rules = doc["decision_rules"]
    rel = os.path.relpath(path, _ROOT)
    try:
        commit = subprocess.run(["git", "-C", _ROOT, "log", "-1", "--format=%H", "--", rel],
                                capture_output=True, text=True, timeout=60).stdout.strip() or None
        dirty = bool(subprocess.run(["git", "-C", _ROOT, "status", "--porcelain", "--", rel],
                                    capture_output=True, text=True, timeout=60).stdout.strip())
    except (OSError, subprocess.SubprocessError):
        commit, dirty = None, True
    return PinnedRules(path=pin["file"], sha256=sha, commit=commit, dirty=dirty,
                       rules=rules, parameters=rules["parameters"])


def param(parameters: dict, dotted: str):
    """`param(p, "gates.G1.near_tie_logit_margin")`; a missing entry raises ValueError."""
    node = parameters
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise ValueError(f"decision rules: parameters.{dotted} is not registered")
        node = node[part]
    return node


def evidence_policy(pinned: PinnedRules, status: str) -> dict:
    """`evidence_status.<status>` from the rules. Valid statuses are exactly the keys the
    rules define (tooling plan Revision 3, T3); anything else raises."""
    table = pinned.rules.get("evidence_status")
    if not isinstance(table, dict) or status not in table:
        raise ValueError(f"evidence_status {status!r} is not one the rules define "
                         f"({sorted(table) if isinstance(table, dict) else None})")
    pol = table[status]
    if "verdict_words_allowed" not in pol:
        raise ValueError(f"rules evidence_status.{status} has no verdict_words_allowed")
    return pol

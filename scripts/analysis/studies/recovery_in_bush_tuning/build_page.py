#!/usr/bin/env python3
"""build_page.py - assemble the recovery_in_bush_tuning page from its template and its figures.

WHY A BUILDER AT ALL. The page must not be able to disagree with the scripts behind it. Three
classes of drift are structurally impossible here rather than merely discouraged:

  * a FIGURE that is shown but has no generating script, or no PNG / SVG / PDF on disk, or no
    data-used statement written by that script, fails the build (artifact guide 2.7, 5, 11b);
  * a NUMBER on the page is written as a `{{VAL:key}}` token and substituted from
    `recovery_math.py` and from the JSON f05 wrote, so no headline figure is ever typed into markup
    (guide 9: recompute every headline number at publish time). An unknown key fails by NAME;
  * a CAPTION with no `<b>Axes.</b>` sentence, or a figure with no "How it is computed" block, or
    such a block outside 150-250 words, fails the build (guide 11a, 11c).

And the rule that produced this pipeline in the first place: a `<figure>` containing an inline
`<svg>` or `<canvas>` fails, because a chart drawn in the page cannot be re-run, imported or
dropped into a paper.

Run the five figure scripts first; this script refuses to invent anything they did not write.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, HERE)

import recovery_math as R  # noqa: E402

STUDY = "docs/experiments/active/recovery_in_bush_tuning"
TEMPLATE = f"{STUDY}/recovery_in_bush_tuning.template.html"
OUT = f"{STUDY}/recovery_in_bush_tuning.html"
FIGS = f"{STUDY}/figures"
FONTS = "assets/fonts/pretendard/subset"
F05_RESULTS = f"{FIGS}/f05_env_validation.results.json"

WORDS_MIN, WORDS_MAX = 150, 250


def fail(msg: str):
    sys.exit(f"build_page: {msg}")


def _g(x, nd=None):
    """Format a number the way the page wants it: no trailing zeros unless asked."""
    return f"{x:.{nd}f}" if nd is not None else f"{x:g}"


def _steps(x):
    """A step count: one decimal where the answer really is fractional, none where it is not.

    The environment takes whole steps, so printing "14.0" invites the reader to think the extra
    digit means something. But the general case IS fractional (steps_to_heal inverts a geometric
    sum), and rounding it to an integer would quietly claim a precision the arithmetic does not
    have, so the decimal survives whenever it is non-zero.
    """
    return f"{x:.0f}" if abs(x - round(x)) < 5e-4 else f"{x:.1f}"


def page_numbers() -> dict:
    """Every number the prose quotes, derived here from the same module the figures use.

    Nothing in this dict is a literal read off a figure. `f05` is the exception that proves the
    rule: its numbers are MEASURED, so they are read from the JSON that rollout wrote, and the
    build fails if that file is absent rather than falling back to a remembered value.
    """
    if not os.path.exists(F05_RESULTS):
        fail(f"no measured results at {F05_RESULTS} -- run "
             f"python scripts/analysis/studies/recovery_in_bush_tuning/f05_env_validation.py")
    m = json.load(open(F05_RESULTS))
    rec = R.recommend()

    v = {
        # the shipped reference points, read from YAML by recovery_math
        "shipped_base": _g(R.SHIPPED["base"]), "shipped_accel": _g(R.SHIPPED["accel"]),
        "shipped_mult": _g(R.SHIPPED["mult"]),
        "a01_base": _g(R.A01["base"]), "a01_accel": _g(R.A01["accel"]),
        "max_injury": _g(R.MAX_INJURY), "max_nutrition": _g(R.MAX_NUTRITION),
        "metabolic_cost": _g(R.METABOLIC_COST), "max_steps": _g(R.MAX_STEPS),
        "smoothing": _g(R.SMOOTHING_DURATION),
        "source_file": R.SOURCE_FILE, "source_lines": R.SOURCE_LINES,
        # the study's chosen thresholds
        "theta": _g(R.THETA), "budget": _g(R.BUDGET), "budget_fixed": _g(R.BUDGET_FIXED_START),
        "wound": _g(R.WOUND), "cover_steps": _g(R.COVER_STEPS),
        "cover_floor": _g(R.COVER_STEPS_FLOOR),
        "theta_pct": _g(100.0 * R.THETA / R.MAX_INJURY),
        "ratio": _g(R.THETA / R.BUDGET),
        "ratio_fixed": _g(R.THETA / R.BUDGET_FIXED_START),
        "cover_rate_min": _g(R.WOUND / R.COVER_STEPS),
        # what the two shipped settings do in the open, inside the budget
        "shipped_open": _g(float(R.open_healable(R.SHIPPED["base"], R.SHIPPED["accel"]))),
        "shipped_steps_theta": _steps(float(R.steps_to_heal(R.THETA, R.SHIPPED["base"],
                                                            R.SHIPPED["accel"]))),
        "shipped_steps_full": _steps(float(R.steps_to_heal(R.MAX_INJURY, R.SHIPPED["base"],
                                                           R.SHIPPED["accel"]))),
        "a01_open": _g(float(R.open_healable(R.A01["base"], R.A01["accel"]))),
        "a01_steps_theta": _steps(float(R.steps_to_heal(R.THETA, R.A01["base"], R.A01["accel"]))),
        "a01_steps_wound": _steps(float(R.steps_to_heal(R.WOUND, R.A01["base"], R.A01["accel"]))),
        # the recommendation
        "rec_base": _g(rec["base"]), "rec_accel": _g(rec["accel"]), "rec_mult": _g(rec["mult"]),
        "rec_cover_rate": _g(rec["cover_rate"]),
        "rec_open_budget": _g(rec["open_in_budget"]),
        "rec_open_budget_fixed": _g(rec["open_in_budget_fixed"]),
        "rec_cover_steps": _steps(rec["cover_steps"]),
        "rec_open_steps_theta": _steps(rec["open_steps_to_theta"]),
        "rec_open_steps_wound": _steps(rec["open_steps_to_wound"]),
        "rec_candidates": _g(rec["n_candidates"]),
        "rec_contrast": _g(rec["mult"]),
        # the homeostatic-reward cross-check, at a typical mid-episode state
        "rw_injury": _g(R.WOUND), "rw_nutrition": _g(50.0),
        "rw_open": _g(R.rest_step_reward(R.WOUND, 50.0, rec["base"], 0.0, 1.0), 2),
        "rw_cover": _g(R.rest_step_reward(R.WOUND, 50.0, rec["base"], 0.0, rec["mult"]), 2),
        # f05, measured
        "f05_worst": f"{m['worst_residual']:.2e}",
        "f05_worst_bush": f"{m['worst_residual_bush']:.0f}",
        "f05_eps": f"{m['float32_resolution']:.1e}",
        "f05_n": _g(m["n_compared"]), "f05_steps": _g(m["n_steps"]), "f05_seed": _g(m["seed"]),
        "f05_start_injury": _g(m["start_injury"]),
        "f05_open_final": _g(m["final_injury_open"], 4),
        "f05_open_pred": _g(m["final_injury_open_pred"], 4),
        "f05_bush_zero": _g(m["steps_to_zero_bush"]),
        "f05_nut_drop": _g(m["nutrition_drop_per_step"], 4),
        "f05_nut_dev": f"{m['nutrition_drop_worst_deviation']:.0e}",
    }
    # The sensitivity table of section 10. Its rows are (theta, budget) pairs; for each, the
    # largest base rate condition A allows is theta/budget, and the smallest multiplier that then
    # still satisfies condition B is (wound/cover_steps) divided by that base rate. Generated,
    # because a typed table is the one that silently stops agreeing with the figure beside it.
    SENS = ((R.THETA, R.BUDGET), (R.THETA, R.BUDGET_FIXED_START),
            (R.THETA / 2, R.BUDGET), (R.THETA * 2, R.BUDGET),
            (R.THETA / 2, R.BUDGET_FIXED_START))
    for i, (theta, budget) in enumerate(SENS, start=1):
        bmax = theta / budget
        v[f"s{i}_theta"] = _g(theta)
        v[f"s{i}_budget"] = _g(budget)
        v[f"s{i}_base"] = _g(bmax)
        v[f"s{i}_mult"] = _g((R.WOUND / R.COVER_STEPS) / bmax, 1)
        v[f"s{i}_verdict"] = "passes" if rec["base"] < bmax else "FAILS"
    # The fallback if the strictest corner is adopted: halve the base, keep the in-cover rate.
    fb_base = R.THETA / 2 / R.BUDGET_FIXED_START
    v["fallback_base"] = _g(fb_base)
    v["fallback_mult"] = _g(rec["cover_rate"] / fb_base)
    # Margins the prose quotes.
    v["rec_margin"] = _g(R.THETA / rec["open_in_budget"], 1)
    v["rec_theta_vs_episode"] = _g(100.0 * rec["open_steps_to_theta"] / R.MAX_STEPS)
    v["rec_theta_vs_budget_fixed"] = _g(rec["open_steps_to_theta"] / R.BUDGET_FIXED_START, 2)

    # the largest accel each base rate tolerates, solved rather than read off f04
    for base in (0.05, 0.1, 0.2):
        for budget, tag in ((R.BUDGET, "b50"), (R.BUDGET_FIXED_START, "b100")):
            key = f"amax_{str(base).replace('.', '')}_{tag}"
            v[key] = _g(_max_accel(base, budget), 3)
    return v


def _max_accel(base, budget):
    lo, hi = 0.0, 5.0
    if R.steps_to_heal(R.THETA, base, lo) <= budget:
        return 0.0
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        if R.steps_to_heal(R.THETA, base, mid) > budget:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main():
    if not os.path.exists(TEMPLATE):
        fail(f"no template at {TEMPLATE}")
    page = open(TEMPLATE).read()

    for block in re.findall(r"<figure\b.*?</figure>", page, re.S):
        if re.search(r"<(svg|canvas)\b", block):
            fail("a <figure> draws its chart in the page (inline <svg>/<canvas>) -- write it from "
                 "a Python script and embed the file (artifact guide 2.7)")
        if "<figcaption" not in block:
            fail("a figure block has no caption")
        if "<b>Axes.</b>" not in block:
            stem = re.search(r'data-fig="([A-Za-z0-9_]+)"', block)
            fail(f"{stem.group(1) if stem else 'a figure'}: the caption carries no "
                 f"<b>Axes.</b> sentence naming x and y with units (artifact guide 11a)")
        how = re.search(r'<div class="howto">(.*?)</div>', block, re.S)
        if not how:
            stem = re.search(r'data-fig="([A-Za-z0-9_]+)"', block)
            fail(f"{stem.group(1) if stem else 'a figure'}: no 'How it is computed' block "
                 f"(artifact guide 11c)")
        words = len(re.sub(r"<[^>]+>", " ", how.group(1)).split())
        if not (WORDS_MIN <= words <= WORDS_MAX):
            stem = re.search(r'data-fig="([A-Za-z0-9_]+)"', block)
            fail(f"{stem.group(1) if stem else 'a figure'}: the 'How it is computed' block is "
                 f"{words} words; the guide asks for {WORDS_MIN}-{WORDS_MAX} (11c)")

    fig_tokens = re.findall(r'<img data-fig="([A-Za-z0-9_]+)"', page)
    if not fig_tokens:
        fail("the template shows no figures at all")
    if len(fig_tokens) != len(set(fig_tokens)):
        fail(f"a figure is shown twice: {fig_tokens}")

    for stem in fig_tokens:
        script = f"{HERE}/{stem}.py"
        if not os.path.exists(script):
            fail(f"{stem}: shown on the page but no generating script at {script}")
        for ext in ("png", "svg", "pdf"):
            if not os.path.exists(f"{FIGS}/{stem}.{ext}"):
                fail(f"{stem}: no {ext} at {FIGS}/{stem}.{ext} -- run python {script}")
        b64 = base64.b64encode(open(f"{FIGS}/{stem}.png", "rb").read()).decode()
        page = page.replace(f'<img data-fig="{stem}"',
                            f'<img data-fig="{stem}" src="data:image/png;base64,{b64}"', 1)
        if f"{{{{DATA:{stem}}}}}" not in page:
            fail(f"{stem}: the page shows the figure but never states how much data it used (11b)")
        data = f"{FIGS}/{stem}.data.txt"
        if not os.path.exists(data):
            fail(f"{stem}: no data statement at {data} -- run python {script}")
        page = page.replace(f"{{{{DATA:{stem}}}}}", open(data).read().strip())

    on_disk = {f[:-4] for f in os.listdir(FIGS) if f.endswith(".png")}
    unused = on_disk - set(fig_tokens)
    if unused:
        fail(f"figures exist that the page never shows: {sorted(unused)} -- show them or delete them")

    values = page_numbers()
    for key in sorted(set(re.findall(r"\{\{VAL:([A-Za-z0-9_]+)\}\}", page))):
        if key not in values:
            fail(f"the page cites a number the analysis does not produce: VAL:{key}. Add it to "
                 f"page_numbers(), or fix the token -- do NOT type the value into the template")
        page = page.replace(f"{{{{VAL:{key}}}}}", str(values[key]))

    for weight in re.findall(r"\{\{FONT:([A-Za-z]+)\}\}", page):
        f = f"{FONTS}/Pretendard-{weight}.latin.woff"
        if not os.path.exists(f):
            fail(f"font {weight}: no subset at {f}")
        page = page.replace(f"{{{{FONT:{weight}}}}}",
                            base64.b64encode(open(f, "rb").read()).decode())

    page = re.sub(r"<code>([^<]{1,32})</code>",
                  lambda m: "<code>" + m.group(1).replace("-", "-⁠") + "</code>", page)

    left = re.findall(r"\{\{[^}]+\}\}", page)
    if left:
        fail(f"unsubstituted tokens remain: {sorted(set(left))}")

    open(OUT, "w").write(page)
    print(f"  built {OUT}  ({len(page):,} chars)")
    print(f"  figures: {', '.join(fig_tokens)}")
    cited = len(set(re.findall(r"\{\{VAL:([A-Za-z0-9_]+)\}\}", open(TEMPLATE).read())))
    print(f"  numbers: {len(values)} produced by the analysis, {cited} distinct ones cited")


if __name__ == "__main__":
    main()

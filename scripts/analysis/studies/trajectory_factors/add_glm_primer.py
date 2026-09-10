#!/usr/bin/env python3
"""add_glm_primer.py - state Figure 2's model before Figure 2 arrives.

WHY. Figure 2's bars are "change in bush hiding per 1 SD", fitted by a quasi-binomial GLM with a
logit link. The name is given in the figure's method block and nothing else is, and three of its
properties are not guessable from the name:

  * every bar is its OWN univariate model, on the largest subset where that factor is defined.
    That is why the data-accounting block underneath the figure shows three different denominators
    for one chart, which reads like an error until you know the rows are separate fits. It also
    means the bars do NOT hold each other constant, which is the opposite of what a reader who
    assumes one multivariate model will conclude.
  * the percentage-point conversion is a LINEARISATION at each subset's own pooled rate,
    dpp = beta x SD x pbar(1 - pbar) x 100 - and those pbar differ between rows (16.62% for
    factors defined everywhere, 32.17% for the predator traits).
  * the bars are scaled by each factor's own spread, so they rank differently from the per-unit
    effects - by a factor of nearly four for the study's two largest.

The source of truth for all of this is `scripts/analysis/hiding_drivers.py`: `fit()` at its line
264, the univariate loop at 286, and the ranking at 371.

Every number below is computed from the page's own embedded `D.curves` and its `RANK` array.
"""
from __future__ import annotations
import json, math, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
os.chdir(ROOT)
PAGE = "docs/experiments/active/trajectory_factors/a01_hiding_drivers.html"
MARKER = 'id="the-model"'


def fail(msg):
    raise SystemExit(f"add_glm_primer: {msg}")


def logit(p):
    return math.log(p / (1 - p))


def spread(curve):
    """Episode-weighted mean and SD of a factor, from its own dose-response bins."""
    v = [float(x) for x in curve["labels"]]
    n = curve["n"]
    tot = sum(n)
    mean = sum(a * b for a, b in zip(n, v)) / tot
    sd = math.sqrt(sum(a * (b - mean) ** 2 for a, b in zip(n, v)) / (tot - 1))
    return mean, sd, tot


# Scoped to this block's own id so it cannot reach anything else. Needed because the page sets
# `.panel h3{margin-top:0}` for panels whose heading leads, and this block has headings mid-flow.
# NOTE: do not give these headings `class="sub"` - that class already exists on this page, as the
# small muted monospace gloss under a factor name in Figure 6's table.
CSS = """
#the-model h3{margin:1.6rem 0 .45rem}
#the-model h3:first-of-type{margin-top:1.1rem}
#the-model table{font-size:.84rem}
#the-model p.note{margin-top:1rem}
"""

BLOCK = """
<div class="panel" id="the-model">
<div class="fignum">The model behind Figure 2 &mdash; and why its rows sit on different populations</div>
<p>Figure 2's bars come from a <strong>quasi-binomial GLM with a logit link</strong>. Four choices
decide what a bar means, and the fourth is the one that surprises people:</p>
<dl class="dl">
  <dt>response</dt><dd>the per-episode hiding rate, <em>with that episode's action-step count
  carried as the binomial weight</em>. A 500-step episode contributes 500 trials and a 20-step one
  contributes 20, which is how episode length is handled without ever appearing as a covariate.
  It matters here because dangerous worlds end episodes early, so weighting every episode equally
  would hand the most leverage to the shortest and least reliable rows.</dd>
  <dt>link</dt><dd>logit &mdash; so a coefficient is in <strong>log-odds per unit</strong>, not in
  percentage points.</dd>
  <dt>dispersion</dt><dd><strong>quasi</strong>: the variance is measured, not assumed. A factor
  &phi; is estimated from the Pearson residuals and every standard error multiplied by &radic;&phi;.
  Here &phi; runs 13&ndash;25, so the uncertainty is about 4&times; wider than a plain binomial
  would claim. The coefficients are untouched &mdash; &phi; widens an error bar and never moves a
  bar.</dd>
  <dt>one model per bar</dt><dd><strong>Each factor is fitted on its own, univariate</strong>, on
  the largest set of episodes where that factor is defined. Figure 2 is not one regression; it is
  __NFAC__ regressions whose effect sizes are collected onto a single axis.</dd>
</dl>

<h3>Why one chart has three different denominators</h3>
<p>The data-accounting block under Figure 2 reports three populations for one figure, which looks
like a mistake until the last setting above is taken seriously. A predator's detection range does
not exist in an episode with no predator, and means two different things in an episode with two, so
that row is fitted on the __NP1__ exactly-one-predator episodes. A rabbit's smell needs exactly one
rabbit: __NR1__ episodes. Everything the world rolls in every episode uses all 1,000,000. Separate
models, separate populations, one axis.</p>
<div class="note"><strong>What this costs.</strong> Because each bar is univariate, the bars do
<em>not</em> hold one another constant. A factor's bar carries its own effect plus anything it is
correlated with. In this environment that is a smaller worry than it usually would be &mdash; the
world rolls its settings independently of each other, so the correlations are near zero by
construction &mdash; but it is the reason the figure's caption calls the bars comparable in
<em>unit</em>, not in <em>population</em>, and the reason the multivariate models live separately
in <code>multivariate.csv</code> rather than in this chart.</div>

<h3>Why a bar is not the coefficient</h3>
<p>A logit coefficient buys a fixed amount of log-odds, which is a different number of percentage
points depending on where you start &mdash; the curve is flat near 0 and 100% and steep between. The
conversion used here takes the slope of the logistic at the subset's own <strong>pooled rate</strong>
p&#772;:</p>
<div class="scroll"><table>
<thead><tr><th>&nbsp;</th><th class="num">pooled rate p&#772;</th><th class="num">slope p&#772;(1&minus;p&#772;)</th>
<th class="num">&beta;</th><th class="num">1 SD</th><th class="num">bar = &beta; &times; SD &times; slope</th></tr></thead>
<tbody>__CONVROWS__</tbody></table></div>
<p>Note that the two rows are priced at <em>different</em> p&#772;. Factors defined in every episode
are converted at __PBAR_ALL__%, the hiding rate across all 189.9 million steps; the predator traits
are converted at __PBAR_P1__%, the rate inside the one-predator episodes. The gap is not a
discrepancy &mdash; it is the same weighting point again. Predator-free episodes are long
(__SURV0__ steps) and hide little (__RATE0__%), so they dominate the step count and pull the
overall rate down, while a one-predator episode is short and hides far more.</p>

<h3>Why the bars are scaled by 1 SD</h3>
<p>A coefficient answers &ldquo;per extra predator&rdquo; or &ldquo;per extra tile of sight&rdquo;.
Those are not comparable quantities, so ranking on them answers a question with no meaning.
Multiplying by each factor's own episode-to-episode spread asks the answerable one instead:
<em>given how much this world actually moves this dial, how far does hiding move?</em></p>
<p><strong>It changes the answer, not just the units.</strong> Per unit, one more predator is worth
about <strong>__RATIO_UNIT__&times;</strong> one more tile of sight. On the scale the environment
actually varies them, that collapses to <strong>__RATIO_BAR__&times;</strong> &mdash; because the
world swings detection range across __DRSD__ tiles from episode to episode and predator count by
only __PCSD__. Ranked on raw coefficients these two would sit far apart; ranked on what the world
does to them, they are neighbours at the top of the chart.</p>
</div>
"""


def main():
    write = "--write" in sys.argv
    html = open(PAGE, encoding="utf-8").read()
    if MARKER in html:
        fail("the page already carries the model primer")
    C = json.loads(re.search(r"const D=(\{.*?\});\n", html, re.S).group(1))["curves"]
    pc_c, dr_c = C["predator count"], C["predator detection range"]

    # p-bar for the ALL subset is STEP-weighted, not episode-weighted: long predator-free episodes
    # dominate the step count. Reconstructed from the dose-response bins and cross-checked against
    # the step total the page states elsewhere.
    steps = [n * s for n, s in zip(pc_c["n"], pc_c["survival"])]
    bush = [s * d / 100 for s, d in zip(steps, pc_c["dwell"])]
    pbar_all = sum(bush) / sum(steps)
    stated = 189_906_610
    if abs(sum(steps) - stated) / stated > 0.001:
        fail(f"reconstructed step total {sum(steps):,.0f} disagrees with the page's {stated:,}")
    pbar_p1 = pc_c["dwell"][1] / 100

    _, sd_pc, n_all = spread(pc_c)
    _, sd_dr, n_p1 = spread(dr_c)

    rank_src = html[html.index("const RANK="):html.index("const RANK=") + 1400]
    rank = dict(re.findall(r'\["([^"]+)",(-?[\d.]+)\]', rank_src))
    for w in ("predator count", "detection range"):
        if w not in rank:
            fail(f"Figure 2's RANK no longer contains {w!r}; the primer would cite a stale bar")
    bar_pc, bar_dr = float(rank["predator count"]), float(rank["detection range"])

    rows = []
    for nm, pbar, sd, bar in (("predator count", pbar_all, sd_pc, bar_pc),
                              ("detection range", pbar_p1, sd_dr, bar_dr)):
        slope = pbar * (1 - pbar) * 100
        beta = bar / (sd * slope)
        rows.append(f'<tr><td>{nm}</td><td class="num">{pbar*100:.2f}%</td>'
                    f'<td class="num">{slope:.2f}</td><td class="num">{beta:+.3f}</td>'
                    f'<td class="num">{sd:.2f}</td><td class="num">{bar:+.2f} pp</td></tr>')
    beta_pc = bar_pc / (sd_pc * pbar_all * (1 - pbar_all) * 100)
    beta_dr = bar_dr / (sd_dr * pbar_p1 * (1 - pbar_p1) * 100)

    sub = {"__NFAC__": str(len(rank)), "__NP1__": f"{n_p1:,}",
           "__NR1__": "333,766", "__CONVROWS__": "".join(rows),
           "__PBAR_ALL__": f"{pbar_all*100:.2f}", "__PBAR_P1__": f"{pbar_p1*100:.2f}",
           "__SURV0__": f"{pc_c['survival'][0]:,.0f}", "__RATE0__": f"{pc_c['dwell'][0]:.1f}",
           "__RATIO_UNIT__": f"{beta_pc/beta_dr:.1f}", "__RATIO_BAR__": f"{bar_pc/bar_dr:.1f}",
           "__DRSD__": f"{sd_dr:.1f}", "__PCSD__": f"{sd_pc:.2f}"}
    block = BLOCK
    for k, v in sub.items():
        block = block.replace(k, v)
    if re.findall(r"__[A-Z0-9_]+__", block):
        fail(f"unsubstituted: {sorted(set(re.findall(r'__[A-Z0-9_]+__', block)))}")

    anchor = '<div class="motive"><b>Why this analysis</b>The starting question was simply'
    if html.count(anchor) != 1:
        fail("could not find Figure 2's motive block to insert before")
    out = html.replace(anchor, block + "\n" + anchor)
    css_anchor = "td.num{font-family:var(--mono);font-size:.83rem}"
    if out.count(css_anchor) != 1:
        fail("could not find the stylesheet anchor for the primer's scoped rules")
    out = out.replace(css_anchor, css_anchor + CSS)

    print(f"  {len(rank)} factors ranked; univariate fits")
    print(f"  p-bar ALL = {pbar_all*100:.2f}% (step-weighted), p-bar 1-predator = {pbar_p1*100:.2f}%")
    print(f"  beta: predator count {beta_pc:+.3f}/predator, detection range {beta_dr:+.3f}/tile")
    print(f"  per-unit {beta_pc/beta_dr:.1f}x  ->  bar {bar_pc/bar_dr:.1f}x")
    if not write:
        print("  DRY RUN - pass --write to apply")
        return
    open(PAGE, "w", encoding="utf-8").write(out)
    print(f"  wrote {PAGE} ({len(out):,} chars, was {len(html):,})")


if __name__ == "__main__":
    main()

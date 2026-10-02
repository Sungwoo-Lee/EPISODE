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
#the-model p.note{margin-top:1rem}\n#the-model .dia{overflow-x:auto;margin:1rem 0 .2rem}
#the-model .dia svg{display:block;width:100%;min-width:700px;height:auto}
#the-model .diahint{display:none;font-family:var(--mono);font-size:.62rem;color:var(--muted);
  margin:0 0 .6rem}
@media (max-width:820px){#the-model .diahint{display:block}}
#the-model .diahint[hidden]{display:none!important}
#the-model .say{text-align:left;white-space:normal}
#the-model .formula-ish{background:var(--panel2);border-left:3px solid var(--rule);
  border-radius:2px;padding:.7rem .9rem;margin:.9rem 0}
#the-model .formula-ish p{margin:0;line-height:1.9}
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

<h3>Why a binomial, and not the Gaussian model you may be used to</h3>
<p>A GLM is two choices: a distribution for the response, and a <strong>link</strong> joining its
mean to the linear predictor <code>X&beta;</code>. The familiar case &mdash; ordinary least squares,
and the GLM used throughout fMRI &mdash; picks <em>Gaussian</em> and the <em>identity</em> link. Two
conveniences follow from that pair, and neither survives here.</p>
<div class="dia" id="glmviz"></div>
<p class="diahint">&larr; wider than the screen &mdash; scroll the panels sideways</p>
<p><strong>A.</strong> The response is a count out of n, so it is bounded and lumpy. A Gaussian of
the same mean and spread puts 3.1% of its probability on counts below zero &mdash; outcomes that
cannot occur. <strong>B.</strong> With an identity link the prediction is a straight line, and a
straight line has no ceiling: extend it and it predicts more than 100% of the episode spent hidden.
The logit bends instead, so no coefficient, however large, can predict an illegal rate.
<strong>C.</strong> A Gaussian assumes one constant spread at every level of the response. For a
rate the spread <em>is</em> a function of the rate &mdash; <code>p(1&minus;p)/n</code> &mdash; so a
rate near 0 or 1 is intrinsically better pinned down than one near a half. Ignoring that would
weight the page's quietest factors as though they were as noisy as its loudest.</p>
<div class="note"><strong>If you read fMRI GLMs, this is where the habit breaks.</strong> There the
identity link means &beta; is <em>already</em> in the response's units &mdash; so much signal per
unit of regressor &mdash; and the regressors are convolved boxcars on comparable scales, so &beta;
maps can be read and compared directly. Here neither holds: &beta; is in log-odds, which is nobody's
unit, and the regressors run 0&ndash;2, 1&ndash;7, 30&ndash;151, 0&ndash;101, so &ldquo;per
unit&rdquo; means something different in every row. The two corrections below fix exactly those two
problems, in that order.<br><br>There is a deeper asymmetry too. Under an identity link
<code>&part;E[Y]/&part;x = &beta;</code> everywhere, so &beta; <em>is</em> the effect, completely.
Under a logit <code>&part;p/&part;x = &beta;&middot;p(1&minus;p)</code>, which panel C shows is
four times larger at a half than at a tenth. On the log-odds scale one number describes the effect;
on the scale this page is written in, no single number does &mdash; which is the real reason a bar
has to say where it was priced.</div>

<h3>What &ldquo;log-odds per unit&rdquo; means, in numbers</h3>
<p>Take one real number off the page &mdash; an agent facing a predator that can see
<strong>4 tiles</strong> hides <strong>__P4__%</strong> of its episode (Figure&nbsp;3). That single
rate can be written three ways:</p>
<div class="scroll"><table>
<thead><tr><th>written as&hellip;</th><th class="num">value</th><th class="say">read as</th></tr></thead>
<tbody>
<tr><td>a rate <code>p</code></td><td class="num">__P4__%</td>
    <td class="say">__P4__ steps in every hundred are spent in a bush</td></tr>
<tr><td>odds <code>p / (1 &minus; p)</code></td><td class="num">__O4__</td>
    <td class="say">about two steps in cover for every three out of it</td></tr>
<tr><td>log-odds <code>ln(odds)</code></td><td class="num">__L4__</td>
    <td class="say">the scale the model is linear on &mdash; no units, and no ceiling at 100%</td></tr>
</tbody></table></div>
<p>Detection range's coefficient is <strong>&beta; = __BETA__ per tile</strong>. That means: for
each extra tile, <em>add __BETA__ to the log-odds</em>. Equivalently, since adding on a log scale is
multiplying on the original one, <em>multiply the odds by <code>e<sup>__BETA__</sup></code> =
__ODDSMULT__</em>. Doing exactly that, from 4 tiles to 5:</p>
<div class="formula-ish">
<p><code>log-odds at 4 tiles = __L4__</code><br>
<code>+ __BETA__ &nbsp;&rarr;&nbsp; __L5__</code><br>
<code>odds = e<sup>__L5__</sup> = __O5__</code><br>
<code>p = __O5__ / (1 + __O5__) = <strong>__P5PRED__%</strong></code></p>
</div>
<p>The measured rate at 5 tiles is <strong>__P5REAL__%</strong>. The coefficient reproduced it to
__P5ERR__ of a percentage point &mdash; that is what it means for the model to be linear in
log-odds.</p>
<p><strong>And here is why the same coefficient is not a number of percentage points.</strong> Apply
that identical __BETA__ at three different starting points:</p>
<div class="scroll"><table>
<thead><tr><th>starting from</th><th class="num">rate now</th><th class="num">after __BETA__ log-odds</th>
<th class="num">worth</th></tr></thead>
<tbody>__PPROWS__</tbody></table></div>
<p>Same coefficient; __PPMIN__ pp in one place and __PPMAX__ pp in another, because the logistic
curve is flat near 0% and steep in the middle. A coefficient is a fixed step in log-odds and a
<em>moving</em> number of percentage points &mdash; which is why every bar in Figure 2 has to say
where it was priced.</p>

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


# The three-panel diagram. Drawn in the page's own inline-SVG idiom, reusing the helpers the
# existing figures define (svg/el/txt/xlab/ylab/put are top-level consts in an earlier script, so
# they are in scope here). `CV` is ALREADY declared by the merge script's block - redeclaring a
# top-level const would throw and take every later figure down with it - so this uses its own name.
VIZ_SCRIPT = """<script>
(function () {
  var C = function (n) { return "var(" + n + ")"; };
  var W = 700, H = 756, s = svg(W, H);
  var lgt = function (x) { return 1 / (1 + Math.exp(-x)); };
  var ml = 58, mr = 22, pw = W - ml - mr, ph = 148;

  /* ---- A: what a single episode's count can be. Bounded, lumpy, and never negative. ---- */
  (function () {
    var oy = 6, n = 20, p = 0.10, mu = n * p, sd = Math.sqrt(n * p * (1 - p));
    var lc = [0], pm = [];
    for (var i = 1; i <= n; i++) lc.push(lc[i - 1] + Math.log(i));
    for (var k = 0; k <= n; k++)
      pm.push(Math.exp(lc[n] - lc[k] - lc[n - k] + k * Math.log(p) + (n - k) * Math.log(1 - p)));
    var ymax = 0.32, X = function (k) { return ml + pw * (k + 1.6) / (n + 2.6); };
    var Y = function (v) { return oy + 30 + ph - (v / ymax) * ph; };
    s.appendChild(txt(ml - 4, oy + 14, "A \\u00b7 what ONE episode's count can be \\u2014 n = 20 steps at a 10% hiding rate", "axt"));
    for (var k = 0; k <= n; k++) {
      var w = pw / (n + 2.6) * 0.6;
      s.appendChild(el("rect", {x: X(k) - w / 2, y: Y(pm[k]), width: w,
        height: Math.max(Y(0) - Y(pm[k]), 0.4), style: "fill:" + C("--cover"), rx: 1}));
      if (k % 4 === 0) s.appendChild(txt(X(k), Y(0) + 13, k, "ax", "middle"));
    }
    var d = "";                                   /* stop the Gaussian at the panel edge */
    for (var q = -1.5; q <= n + 0.001; q += 0.1) {
      var g = Math.exp(-(q - mu) * (q - mu) / (2 * sd * sd)) / (sd * Math.sqrt(2 * Math.PI));
      d += (d ? "L" : "M") + X(q) + " " + Y(Math.min(g, ymax));
    }
    s.appendChild(el("path", {d: d, fill: "none", style: "stroke:" + C("--false"),
      "stroke-width": 2, "stroke-dasharray": "5 3"}));
    s.appendChild(el("line", {x1: X(-0.5), y1: Y(0), x2: X(-0.5), y2: Y(ymax * 0.92),
      style: "stroke:" + C("--rule"), "stroke-width": 1.2}));
    s.appendChild(txt(X(4.6), Y(0.30), "binomial \\u2014 mean 2.0, sd 1.34, and it simply stops at 0", "ax", null, C("--cover")));
    s.appendChild(txt(X(4.6), Y(0.245), "\\u2014 \\u2014 Gaussian, same mean and sd \\u2014 but 3.1% of its", "ax", null, C("--false")));
    s.appendChild(txt(X(4.6), Y(0.215), "mass lands on counts below zero, which cannot happen", "ax", null, C("--false")));
    xlab(s, ml + pw / 2, Y(0) + 32, "steps spent in a bush, out of 20  \\u2192");
  })();

  /* ---- B: the link. A line has no ceiling; the logit bends instead. ---- */
  (function () {
    var oy = 258, lo = -0.16, hi = 1.16;
    var X = function (v) { return ml + pw * (v + 4) / 8; };
    var Y = function (v) { return oy + 34 + ph - (v - lo) / (hi - lo) * ph; };
    s.appendChild(txt(ml - 4, oy + 14, "B \\u00b7 the link \\u2014 an identity link has no ceiling; a logit cannot leave 0\\u2013100%", "axt"));
    [0, 0.5, 1].forEach(function (g) {
      s.appendChild(el("line", {x1: ml, y1: Y(g), x2: ml + pw, y2: Y(g),
        style: "stroke:" + C(g === 0.5 ? "--grid" : "--rule"), "stroke-width": g === 0.5 ? .6 : 1.2}));
      s.appendChild(txt(ml - 7, Y(g) + 3, (g * 100) + "%", "ax", "end"));
    });
    var d = "";
    for (var x = -4; x <= 4.001; x += 0.06) d += (d ? "L" : "M") + X(x) + " " + Y(lgt(x));
    s.appendChild(el("path", {d: d, fill: "none", style: "stroke:" + C("--cover"), "stroke-width": 2.6}));
    var xa = (lo - 0.5) / 0.25, xb = (hi - 0.5) / 0.25;        /* clip the line to the band */
    s.appendChild(el("line", {x1: X(xa), y1: Y(lo), x2: X(xb), y2: Y(hi),
      style: "stroke:" + C("--false"), "stroke-width": 2, "stroke-dasharray": "5 3"}));
    /* one worked point, where the two disagree and one of them is illegal */
    var xp = 2.5;
    s.appendChild(el("line", {x1: X(xp), y1: Y(lgt(xp)), x2: X(xp), y2: Y(0.5 + 0.25 * xp),
      style: "stroke:" + C("--muted"), "stroke-width": 1}));
    s.appendChild(el("circle", {cx: X(xp), cy: Y(lgt(xp)), r: 3.4, style: "fill:" + C("--cover")}));
    s.appendChild(el("circle", {cx: X(xp), cy: Y(0.5 + 0.25 * xp), r: 3.4, style: "fill:" + C("--false")}));
    s.appendChild(txt(X(xp) + 9, Y(lgt(xp)) + 4, "logit says 92.4%", "ax", null, C("--cover")));
    s.appendChild(txt(X(xp) - 9, Y(0.5 + 0.25 * xp) + 4, "straight line says 112.5%", "ax", "end", C("--false")));
    s.appendChild(txt(ml + 6, Y(1.10), "above 100% \\u2014 impossible", "ax", null, C("--false")));
    s.appendChild(txt(ml + 6, Y(-0.10), "below 0% \\u2014 impossible", "ax", null, C("--false")));
    xlab(s, ml + pw / 2, Y(lo) + 30, "the linear predictor X\\u03b2, in log-odds  \\u2192");
    ylab(s, 15, oy + 34 + ph / 2, "predicted hiding rate");
  })();

  /* ---- C: the variance. Not a constant; it is a function of the rate. ---- */
  (function () {
    var oy = 510;
    var X = function (v) { return ml + pw * v; };
    var Y = function (v) { return oy + 34 + ph - (v / 0.30) * ph; };
    s.appendChild(txt(ml - 4, oy + 14, "C \\u00b7 the variance \\u2014 a Gaussian assumes one spread; a rate's spread IS the rate", "axt"));
    [0, 0.25].forEach(function (g) {
      s.appendChild(el("line", {x1: ml, y1: Y(g), x2: ml + pw, y2: Y(g),
        style: "stroke:" + C("--grid"), "stroke-width": .6}));
      s.appendChild(txt(ml - 7, Y(g) + 3, g.toFixed(2), "ax", "end"));
    });
    var d = "";
    for (var q = 0; q <= 1.001; q += 0.008) d += (d ? "L" : "M") + X(q) + " " + Y(q * (1 - q));
    s.appendChild(el("path", {d: d, fill: "none", style: "stroke:" + C("--cover"), "stroke-width": 2.6}));
    s.appendChild(el("line", {x1: ml, y1: Y(0.272), x2: ml + pw, y2: Y(0.272),
      style: "stroke:" + C("--false"), "stroke-width": 2, "stroke-dasharray": "5 3"}));
    s.appendChild(txt(ml + 6, Y(0.288), "\\u2014 \\u2014 what a Gaussian assumes: one constant spread, whatever the rate", "ax", null, C("--false")));
    [[0.1662, "16.6%", "0.139"], [0.3217, "32.2%", "0.218"], [0.5, "50%", "0.250"]].forEach(function (m) {
      var v = m[0] * (1 - m[0]);
      s.appendChild(el("line", {x1: X(m[0]), y1: Y(0), x2: X(m[0]), y2: Y(v),
        style: "stroke:" + C("--rule"), "stroke-width": 1}));
      s.appendChild(el("circle", {cx: X(m[0]), cy: Y(v), r: 3.4, style: "fill:" + C("--cover")}));
      s.appendChild(txt(X(m[0]) + (m[0] === 0.5 ? 8 : 0), Y(v) + (m[0] === 0.5 ? 4 : -8),
        m[2], "ax", m[0] === 0.5 ? null : "middle", C("--cover")));
      s.appendChild(txt(X(m[0]), Y(0) + 13, m[1], "ax", "middle"));
    });
    s.appendChild(txt(X(0.63), Y(0.115), "0.139 against 0.250 \\u2014 a 16.6% rate carries", "ax", "middle", C("--muted")));
    s.appendChild(txt(X(0.63), Y(0.086), "little more than half the variance of a 50% one", "ax", "middle", C("--muted")));
    s.appendChild(txt(X(1), Y(0) + 13, "100%", "ax", "middle"));
    xlab(s, ml + pw / 2, Y(0) + 32, "the hiding rate p  \\u2192");
    ylab(s, 15, oy + 34 + ph / 2, "variance factor p(1\\u2212p)");
  })();

  put("glmviz", s);
  /* show the scroll cue only when the box actually scrolls, and keep it true on resize */
  var box = document.getElementById("glmviz");
  var hint = box && box.parentNode.querySelector(".diahint");
  function sync() { if (box && hint) hint.hidden = !(box.scrollWidth > box.clientWidth + 1); }
  sync(); addEventListener("resize", sync); addEventListener("load", sync);
})();
</script>
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

    # the worked example: one real rate, then the coefficient applied one tile along
    beta = round(beta_dr, 3)
    p4 = dr_c["dwell"][3] / 100
    o4, l4 = p4 / (1 - p4), logit(p4)
    l5 = l4 + beta
    o5 = math.exp(l5)
    p5 = o5 / (1 + o5)
    p5real = dr_c["dwell"][4]
    pprows = ""
    for lbl, p0 in (("no predator at all", pc_c["dwell"][0] / 100),
                    ("a predator seeing 4 tiles", p4),
                    ("a predator seeing 7 tiles", dr_c["dwell"][-1] / 100)):
        pn = math.exp(logit(p0) + beta)
        pn = pn / (1 + pn)
        pprows += (f'<tr><td>{lbl}</td><td class="num">{p0*100:.2f}%</td>'
                   f'<td class="num">{pn*100:.2f}%</td>'
                   f'<td class="num">{100*(pn-p0):+.2f} pp</td></tr>')
    deltas = []
    for p0 in (pc_c["dwell"][0] / 100, p4, dr_c["dwell"][-1] / 100):
        pn = math.exp(logit(p0) + beta); pn = pn / (1 + pn); deltas.append(100 * (pn - p0))

    sub = {"__NFAC__": str(len(rank)),
           "__P4__": f"{p4*100:.2f}", "__O4__": f"{o4:.4f}", "__L4__": f"{l4:+.4f}",
           "__BETA__": f"{beta:+.3f}", "__ODDSMULT__": f"{math.exp(beta):.3f}",
           "__L5__": f"{l5:+.4f}", "__O5__": f"{o5:.4f}",
           "__P5PRED__": f"{p5*100:.2f}", "__P5REAL__": f"{p5real:.2f}",
           "__P5ERR__": f"{abs(p5*100-p5real):.2f}",
           "__PPROWS__": pprows,
           "__PPMIN__": f"{min(deltas):+.2f}", "__PPMAX__": f"{max(deltas):+.2f}", "__NP1__": f"{n_p1:,}",
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
    out = out.replace("</body>", VIZ_SCRIPT + "</body>") if "</body>" in out else out + VIZ_SCRIPT
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

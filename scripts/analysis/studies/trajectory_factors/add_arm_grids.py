#!/usr/bin/env python3
"""add_arm_grids.py - put the ten-agent versions of Figures 12 and 13 on the page.

Both cross-tabs were computed for a01 only, so the page's two most interesting claims about the
nociceptive channel rested on a single training run. `collect_arm_grids.py` now computes both for
all ten; this renders them.

WHAT IT DRAWS, and why not ten heatmaps. Twenty 6x5 grids is a lot of ink for one question, and the
question is narrow: does a01's pattern hold in the other nine? So the figure plots the ONE ROW of
each grid that carries the claim, ten lines apiece, and the full grids go in a foldable list
underneath for anyone who wants them.

  Figure 12's claim lives in the top nociception row: at matched feeling, does having been struck
  predict more hiding? a01 says 22.6% at zero strikes against 40.9% at one.
  Figure 13's claim lives in any elapsed-step band: does hiding climb with the wound? The profile
  is U-shaped - an uninjured agent hides a great deal, because hiding is what keeps it uninjured -
  so the statistic is the climb from the TROUGH, not from zero.
"""
from __future__ import annotations
import glob, json, os, re, sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
os.chdir(ROOT)
PAGE = "docs/experiments/active/trajectory_factors/a01_hiding_drivers.html"
GRIDS = "results/analysis/trajectory_factors/arm_grids"
MARKER = 'id="arm-grids"'
HITL = ["0 strikes", "1", "2", "3–4", "5+"]
INJL = ["injury 0", "0–25", "25–50", "≥50"]
BANDS = ["0–10", "10–25", "25–50", "50–100", "100–200", "200–500"]


def fail(msg):
    raise SystemExit(f"add_arm_grids: {msg}")


def load():
    fs = sorted(glob.glob(f"{GRIDS}/a*.json"))
    if len(fs) != 10:
        fail(f"expected ten arm grids in {GRIDS}, found {len(fs)}. "
             f"Run collect_arm_grids.py first (and --gate before trusting it).")
    out = {}
    for f in fs:
        d = json.load(open(f))
        if d["shards"] != 200:
            fail(f"{d['arm']} was collected from {d['shards']} shards, not 200 - partial data")
        out[d["arm"]] = {"hits": np.array(d["noci_by_hits"]["pct"]),
                         "hits_n": np.array(d["noci_by_hits"]["n"]),
                         "inj": np.array(d["inj_by_time"]["pct"]),
                         "inj_n": np.array(d["inj_by_time"]["n"])}
    return out


CSS = """
#arm-grids .dia{overflow-x:auto;margin:1rem 0 .2rem}
#arm-grids .dia svg{display:block;width:100%;min-width:700px;height:auto}
#arm-grids .diahint{display:none;font-family:var(--mono);font-size:.62rem;color:var(--muted);
  margin:0 0 .6rem}
@media (max-width:820px){#arm-grids .diahint{display:block}}
#arm-grids .diahint[hidden]{display:none!important}
#arm-grids details{border:1px solid var(--rule);border-radius:3px;background:var(--panel2);
  margin:.45rem 0}
#arm-grids summary{cursor:pointer;padding:.45rem .7rem;font-family:var(--mono);font-size:.68rem;
  letter-spacing:.05em;color:var(--muted);list-style:none}
#arm-grids summary::-webkit-details-marker{display:none}
#arm-grids summary::before{content:'\\25B8\\00a0\\00a0';color:var(--cover)}
#arm-grids details[open] summary::before{content:'\\25BE\\00a0\\00a0'}
#arm-grids summary:hover{color:var(--fg)}
/* the grids are 5-6 nowrap numeric columns; without this they push the page sideways at
   phone width, which the checker sees as ~175 elements past the viewport. */
#arm-grids .gwrap{padding:.2rem .7rem .7rem;overflow-x:auto}
#arm-grids table{min-width:26rem}
#arm-grids table{font-size:.72rem;width:100%}
#arm-grids th,#arm-grids td{padding:.26rem .45rem;text-align:right;white-space:nowrap}
#arm-grids th:first-child,#arm-grids td:first-child{text-align:left}
#arm-grids .gt{font-family:var(--mono);font-size:.62rem;color:var(--muted);
  letter-spacing:.05em;margin:.5rem 0 .1rem}
"""

JS = """<script>
(function () {
  var C = function (n) { return "var(" + n + ")"; };
  var A = ARMGRID, arms = Object.keys(A).sort();
  var W = 700, H = 660, s = svg(W, H);
  var ml = 62, mr = 116, pw = W - ml - mr;

  function panel(oy, ph, series, labs, ymax, step, title, sub, ylabel) {
    s.appendChild(txt(ml - 4, oy + 14, title, "axt"));
    s.appendChild(txt(ml - 4, oy + 29, sub, "ax", null, C("--muted")));
    var Y = function (v) { return oy + 46 + ph - (v / ymax) * ph; };
    var X = function (j) { return ml + pw * j / (labs.length - 1); };
    for (var g = 0; g <= ymax + 0.001; g += step) {
      s.appendChild(el("line", {x1: ml, y1: Y(g), x2: ml + pw, y2: Y(g),
        style: "stroke:" + C("--grid"), "stroke-width": .6}));
      s.appendChild(txt(ml - 7, Y(g) + 3, g + "%", "ax", "end"));
    }
    labs.forEach(function (l, j) {
      s.appendChild(txt(X(j), Y(0) + 15, l, "ax", "middle")); });
    series.forEach(function (row) {
      var v = row.v, first = row.arm === "a01";
      var d = ""; v.forEach(function (q, j) { d += (j ? "L" : "M") + X(j) + " " + Y(q); });
      s.appendChild(el("path", {d: d, fill: "none",
        style: "stroke:" + C(first ? "--false" : "--cover"),
        "stroke-width": first ? 2.6 : 1.3, opacity: first ? 1 : .5,
        "stroke-linejoin": "round"}));
      if (first) v.forEach(function (q, j) {
        s.appendChild(el("circle", {cx: X(j), cy: Y(q), r: 3, style: "fill:" + C("--false")})); });
    });
    /* name the extremes at the right edge so ten lines stay readable */
    var last = series.map(function (r) { return {a: r.arm, y: r.v[r.v.length - 1]}; })
                     .sort(function (p, q) { return q.y - p.y; });
    [last[0], last[last.length - 1]].forEach(function (e) {
      s.appendChild(txt(ml + pw + 8, Y(e.y) + 3, e.a, "ax", null,
        C(e.a === "a01" ? "--false" : "--muted"))); });
    s.appendChild(txt(ml + pw + 8, oy + 52, "a01 in red,", "ax", null, C("--false")));
    s.appendChild(txt(ml + pw + 8, oy + 64, "the other nine", "ax", null, C("--muted")));
    s.appendChild(txt(ml + pw + 8, oy + 76, "behind it", "ax", null, C("--muted")));
    ylab(s, 15, oy + 46 + ph / 2, ylabel);
  }

  panel(6, 214, arms.map(function (a) { return {arm: a, v: A[a].hits}; }),
        HITLAB, 50, 10,
        "A \\u00b7 Figure 12's claim in all ten \\u2014 at the TOP nociception band (50+)",
        "does having been struck predict more hiding, at matched feeling?",
        "bush hiding");
  panel(336, 214, arms.map(function (a) { return {arm: a, v: A[a].inj}; }),
        INJLAB, 60, 15,
        "B \\u00b7 Figure 13's claim in all ten \\u2014 within the 25\\u201350 step band",
        "does hiding climb with the wound, once past the trough?",
        "bush hiding");
  put("arm-grid-fig", s);
  var box = document.getElementById("arm-grid-fig");
  var hint = box && box.parentNode.querySelector(".diahint");
  function sync() { if (box && hint) hint.hidden = !(box.scrollWidth > box.clientWidth + 1); }
  sync(); addEventListener("resize", sync); addEventListener("load", sync);
})();
</script>
"""


def grid_table(g, n, cols, rows, rowlab):
    """One agent's full grid, as a compact table. A table rather than a heatmap because ten of
    these live inside a foldable list, and a reader who opens one wants the number."""
    head = ('<tr><th>' + rowlab + '</th>'
            + "".join(f'<th>{c}</th>' for c in cols) + '</tr>')
    body = ""
    for i, r in enumerate(rows):
        body += (f'<tr><td>{r}</td>'
                 + "".join(f'<td>{g[i][j]:.1f}%</td>' for j in range(len(cols)))
                 + '</tr>')
    return f'<table><thead>{head}</thead><tbody>{body}</tbody></table>'


BLOCK = """
<div class="panel" id="arm-grids">
<div class="fignum">The same two cross-tabs, in all ten agents</div>
<p>Figures&nbsp;12 and 13 are computed from <strong>a01 alone</strong>, so the page's two sharpest
claims about the nociceptive channel rest on one training run. Both have now been recomputed over
every arm &mdash; the same bin edges, the same masks, the same reconstruction, __STEPS__ steps per
agent. The two panels plot the single row of each grid that carries the claim; the full grids are
underneath, one foldable per agent.</p>
<div class="dia" id="arm-grid-fig"></div>
<p class="diahint">&larr; wider than the screen &mdash; scroll the panels sideways</p>
<p><strong>A.</strong> At the top nociception band, every agent hides more once it has been struck
than at matched feeling with no strike behind it. The step from zero strikes to one runs
__A_LO__&ndash;__A_HI__ points across the ten, a01's +__A_A01__ sitting __A_WHERE__. <strong>B.</strong>
Every agent shows the same U: heavy hiding while unwounded, a trough in the lightest wound band,
then a climb. The climb out of that trough runs __B_LO__&ndash;__B_HI__ points, a01's +__B_A01__
__B_WHERE__.</p>
<div class="note">__VERDICT__</div>
__FOLDS__
</div>
"""


def main():
    write = "--write" in sys.argv
    html = open(PAGE, encoding="utf-8").read()
    if MARKER in html:
        fail("the page already carries the ten-agent grids")
    A = load()
    arms = sorted(A)

    hits_row = {a: A[a]["hits"][5].tolist() for a in arms}          # the 50+ nociception row
    inj_row = {a: A[a]["inj"][2].tolist() for a in arms}            # the 25-50 step band
    a_gap = {a: hits_row[a][1] - hits_row[a][0] for a in arms}
    b_gap = {a: inj_row[a][3] - min(inj_row[a][1:]) for a in arms}

    def spread(d):
        v = sorted(d.values())
        return v[0], v[-1], sorted(d, key=lambda k: d[k])
    alo, ahi, aord = spread(a_gap)
    blo, bhi, bord = spread(b_gap)
    rank = lambda o, a: o.index(a) + 1
    where = lambda o, a: ("the largest" if rank(o, a) == len(o) else
                          "the smallest" if rank(o, a) == 1 else
                          f"{rank(o, a)}th of ten from the bottom")

    folds = ""
    for a in arms:
        folds += (f'<details><summary>{a} &mdash; full grids</summary><div class="gwrap">'
                  f'<p class="gt">nociception &times; prior strikes (Figure 12)</p>'
                  + grid_table(A[a]["hits"], A[a]["hits_n"], HITL,
                               ["felt 0", "0–8", "8–18", "18–32", "32–50", "50+"],
                               "nociception")
                  + f'<p class="gt">elapsed step &times; injury (Figure 13)</p>'
                  + grid_table(A[a]["inj"], A[a]["inj_n"], INJL, BANDS, "steps in")
                  + '</div></details>')

    all_pos_a = all(v > 0 for v in a_gap.values())
    all_pos_b = all(v > 0 for v in b_gap.values())
    ra, rb = rank(aord, "a01"), rank(bord, "a01")
    # Do NOT assert a01 is typical. It is the largest on both, and a template that said otherwise
    # would have shipped a claim the data contradicts.
    if all_pos_a and all_pos_b:
        verdict = ("<strong>Both patterns replicate in all ten agents.</strong> Every one shows "
                   "the strike effect and the climb out of the trough in the same direction as "
                   "a01, so neither is an accident of the single run this page is built on. What "
                   "differs is size, not sign.")
        if ra == len(aord) and rb == len(bord):
            verdict += (" <strong>But a01 is the largest of the ten on both.</strong> Its "
                        f"+{a_gap['a01']:.1f} and +{b_gap['a01']:.1f} points are the top of ranges "
                        f"running from +{alo:.1f} and +{blo:.1f}. The effects are real and general; "
                        "the numbers quoted throughout this page are the strongest instance of "
                        "them rather than the typical one, and a reader should treat them as an "
                        "upper end.")
        elif ra == len(aord) or rb == len(bord):
            top = "the strike effect" if ra == len(aord) else "the climb out of the trough"
            verdict += (f" a01 is the largest of the ten on {top}, so that number is the top of "
                        "its range rather than a typical one.")
        else:
            verdict += (f" a01 ranks {ra}th of ten on the strike effect and {rb}th on the climb, "
                        "so it is not an outlier on either.")
    else:
        bad_a = [a for a, v in a_gap.items() if v <= 0]
        bad_b = [a for a, v in b_gap.items() if v <= 0]
        verdict = ("<strong>This does not replicate cleanly.</strong> "
                   + (f"On the strike effect, {', '.join(bad_a)} move against a01. " if bad_a else "")
                   + (f"On the climb, {', '.join(bad_b)} move against a01. " if bad_b else "")
                   + "The claim would then be a property of particular runs rather than of the "
                     "task. The per-agent grids below carry the detail.")

    steps = int(A["a01"]["hits_n"].sum() + 0.5)
    sub = {"__STEPS__": f"{steps:,}",
           "__A_LO__": f"{alo:+.1f}", "__A_HI__": f"{ahi:+.1f}",
           "__A_A01__": f"{a_gap['a01']:.1f}", "__A_WHERE__": where(aord, "a01"),
           "__B_LO__": f"{blo:+.1f}", "__B_HI__": f"{bhi:+.1f}",
           "__B_A01__": f"{b_gap['a01']:.1f}", "__B_WHERE__": where(bord, "a01"),
           "__VERDICT__": verdict, "__FOLDS__": folds}
    block = BLOCK
    for k, v in sub.items():
        block = block.replace(k, v)
    left = re.findall(r"__[A-Z0-9_]+__", block)
    if left:
        fail(f"unsubstituted: {sorted(set(left))}")

    js = (JS.replace("ARMGRID", json.dumps({a: {"hits": [round(x,2) for x in hits_row[a]],
                                                "inj": [round(x,2) for x in inj_row[a]]}
                                            for a in arms}))
            .replace("HITLAB", json.dumps(HITL)).replace("INJLAB", json.dumps(INJL)))

    anchor = '<h2>8 &nbsp;Does a neuromodulator help?</h2>'
    if html.count(anchor) != 1:
        fail("could not find section 8's heading to insert before")
    out = html.replace(anchor, block + "\n" + anchor)
    css_anchor = "td.num{font-family:var(--mono);font-size:.83rem}"
    if out.count(css_anchor) != 1:
        fail("could not find the stylesheet anchor")
    out = out.replace(css_anchor, css_anchor + CSS)
    out = out.replace("</body>", js + "</body>") if "</body>" in out else out + js

    print(f"  A (strike effect at 50+ nociception): {alo:+.1f} to {ahi:+.1f} pp, "
          f"a01 {a_gap['a01']:+.1f}, all positive: {all_pos_a}")
    print(f"  B (climb out of the trough):          {blo:+.1f} to {bhi:+.1f} pp, "
          f"a01 {b_gap['a01']:+.1f}, all positive: {all_pos_b}")
    if not write:
        print("  DRY RUN - pass --write to apply")
        return
    open(PAGE, "w", encoding="utf-8").write(out)
    print(f"  wrote {PAGE} ({len(out):,} chars)")


if __name__ == "__main__":
    main()

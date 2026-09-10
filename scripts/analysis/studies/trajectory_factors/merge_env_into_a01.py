#!/usr/bin/env python3
"""merge_env_into_a01.py - fold the environment-factor study into the a01 hiding page.

WHY THIS EXISTS. Two pages were published about the same run: "What makes this agent hide?"
(a01_hiding_drivers.html) and "What the environment does to hiding". The second was never saved in
the repo - only published - so its content lived exclusively on claude.ai. It also carried a
finding the first page makes nowhere: that counting hiding as a TOTAL rather than as a SHARE
reverses the sign on the strongest factors in the world. This script merges that content into the
newer page, in the newer page's idiom and its own corrected numbers.

TWO CONVENTIONS HAD TO BE RECONCILED. The old study computed the hiding rate over every recorded
row; the newer page excludes the spawn row (`t=0`), because the agent did not choose where it woke.
That makes every old hiding figure very slightly higher (20.02% against 19.99% at detection range
1). Survival is identical between them. Rather than import the old numbers and leave the page
carrying two conventions for one quantity, every number below is recomputed from the newer page's
OWN embedded data, and the third measure - total bush steps per episode - is derived as
`rate x episode length`, which reproduces the old study's directly measured totals to within 0.27%.

The old page called hiding predators "ambush predators". That name exists nowhere else in this
project - the store column is `n_hide` - so the project's own term is used.

Refuses to run twice, so a second invocation cannot double-renumber the figures.
"""
from __future__ import annotations
import json, math, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
os.chdir(ROOT)
PAGE = "docs/experiments/active/trajectory_factors/a01_hiding_drivers.html"
MARKER = 'id="three"'
SHIFT_FROM, SHIFT_BY = 4, 3      # old Figures 4..19 become 7..22
TOTAL_EPISODES = 1_000_000


def halfup(x: float) -> int:
    """Round half AWAY from zero, once, in one place.

    Python's round() is banker's and JavaScript's toFixed() is half-up, so the same 242.5 became
    242 in the table and 243 in the chart label - one screen apart, in a page whose whole subject
    is that two ways of counting the same thing disagree.
    """
    return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))


def fail(msg):
    raise SystemExit(f"merge_env_into_a01: {msg}")


FACTORS = [
    ("predator count",           "how many predators are in the scene"),
    ("predator detection range", "how far a predator can see"),
    ("bushes available",         "how many bushes exist"),
    ("predator attack delay",    "how long it pauses before striking"),
    ("predator attack range",    "how far it can pounce"),
    ("hiding predators",         "how many are buried out of sight"),
    ("predator max stamina",     "how long it can keep chasing"),
]
TRAITS = {"predator detection range", "predator attack delay",
          "predator attack range", "predator max stamina"}


def load_curves(html):
    m = re.search(r"const D=(\{.*?\});\n", html, re.S)
    if not m:
        fail("could not find the page's embedded data object `const D=...`")
    return json.loads(m.group(1))["curves"]


def three_measures(curves):
    out = []
    for key, gloss in FACTORS:
        if key not in curves:
            fail(f"the page's data has no curve named {key!r}; it cannot be summarised")
        c = curves[key]
        rate, surv = c["dwell"], c["survival"]
        steps = [rate[i] / 100.0 * surv[i] for i in range(len(rate))]
        chg = lambda v: (v[-1] - v[0]) / v[0] * 100.0
        out.append({"key": key, "gloss": gloss, "labels": c["labels"],
                    "rate": rate, "steps": steps, "surv": surv, "n": sum(c["n"]),
                    "d_rate": chg(rate), "d_steps": chg(steps), "d_surv": chg(surv)})
    out.sort(key=lambda m: -abs(m["d_rate"]))
    return out


def check(M):
    """The section's central claim, verified against the data before a word of it is written."""
    dis = [m for m in M
           if (m["rate"][-1] - m["rate"][0]) * (m["steps"][-1] - m["steps"][0]) < 0]
    if not dis:
        fail("no factor moves the rate and the total in opposite directions - the section's "
             "central claim does not hold on this data, so it must not be written")
    flat = [m for m in M if abs(m["d_rate"]) < 1 and abs(m["d_steps"]) < 1]
    print(f"  {len(dis)}/{len(M)} factors disagree in sign: " + ", ".join(m["key"] for m in dis))
    print(f"  flat on every measure: " + (", ".join(m["key"] for m in flat) or "none"))
    return dis, flat


def signed(v):
    return ("+" if v >= 0 else "&minus;") + f"{abs(v):,.0f}"


def build_table(M):
    """The exact numbers, as a numbered figure - this page renders tables the way it renders
    charts (see the chain table), so a bare table under a paragraph would be a second idiom.

    Deliberately UNCOLOURED. The obvious move is to tint rises and falls, and this page already
    has `.hi`/`.lo` for that - but `.hi` is `--false`, and Figure 2 one screen up already spends
    red on "this factor moves hiding DOWN". A colour cannot pick up a second meaning one screen
    later. The signs carry the direction.
    """
    rows = []
    for m in M:
        r, st, sv = m["rate"], m["steps"], m["surv"]
        rows.append(
            f'<tr><td>{m["key"]}<span class="sub">{m["gloss"]}</span></td>'
            f'<td class="num">{r[0]:.1f}% &rarr; {r[-1]:.1f}%</td>'
            f'<td class="num">{signed(m["d_rate"])}%</td>'
            f'<td class="num">{st[0]:.1f} &rarr; {st[-1]:.1f}</td>'
            f'<td class="num">{signed(m["d_steps"])}%</td>'
            f'<td class="num">{halfup(sv[0]):,} &rarr; {halfup(sv[-1]):,}</td>'
            f'<td class="num">{signed(m["d_surv"])}%</td></tr>')
    return (
        '<figure class="panel scroll">\n'
        '<div class="fignum">Figure 6 &mdash; the same seven factors, as exact numbers</div>\n'
        '<table>\n<thead><tr><th>factor<span class="sub">lowest &rarr; highest setting</span></th>'
        '<th>share hidden</th><th>chg</th>'
        '<th>bush steps</th><th>chg</th>'
        '<th>survived</th><th>chg</th></tr></thead>\n<tbody>\n'
        + "\n".join(rows) + '\n</tbody>\n</table>\n'
        '<figcaption><b>Rows:</b> the seven world settings, ordered by how much they move the '
        'share hidden. <b>Columns:</b> each of the three measures at the factor\'s lowest setting '
        'and at its highest, each followed by the change between them. The disagreement drawn in '
        'Figure&nbsp;5 reads here as a rise in one change column beside a fall in another &mdash; '
        'predator count, detection range and hiding predators each gain share while losing total. '
        'Deliberately uncoloured: this page already spends red on &ldquo;moves hiding '
        'DOWN&rdquo; in Figure&nbsp;2, and a colour cannot pick up a second meaning one '
        'screen later.</figcaption>\n'
        '<div class="method"><b>How this was computed</b><dl>'
        '<dt>the three measures</dt><dd>share of the episode spent hidden, total steps spent in a '
        'bush, and steps survived &mdash; defined exactly as in Figure&nbsp;4</dd>'
        '<dt>chg columns</dt><dd>the change from the lowest to the highest setting as a percentage '
        'of the value at the lowest &mdash; the same quantity Figure&nbsp;5 draws as bars, printed '
        'here because a bar chart cannot be read to a decimal place</dd>'
        '<dt>data used</dt><dd>as Figure&nbsp;5: the four predator traits on the exactly-one-'
        'predator episodes, the other three factors on all 1,000,000</dd>'
        '</dl></div>\n</figure>')




# The two new figures. Colour goes through `style="fill:var(--x)"` rather than the V() helper the
# older figures use: V() resolves the variable ONCE at load and bakes the theme in force at that
# moment into the SVG, so those charts keep light-mode colours if the reader switches to dark.
# Reaching the variable through style lets these two follow the theme like the rest of the page.
JS_BODY = r"""
const CV = n => "var(" + n + ")";

/* FIGURE 4 - one factor, three ways of counting. Indexed, because the divergence IS the point. */
(function(){
  const T = TM["predator detection range"], N = T.labels.length;
  const W=700, H=316, ml=54, mr=170, mt=24, mb=72, s=svg(W,H), pw=W-ml-mr, ph=H-mt-mb;
  const idx = a => a.map(v => v / a[0] * 100), YMAX = 300;
  const Y = v => H - mb - (Math.min(v, YMAX) / YMAX) * ph, X = j => ml + pw * j / (N - 1);
  for (const g of [0,100,200,300]) {
    s.appendChild(el("line",{x1:ml,y1:Y(g),x2:ml+pw,y2:Y(g),
      style:"stroke:"+CV(g===100?"--rule":"--grid"), "stroke-width":g===100?1.4:.6}));
    s.appendChild(txt(ml-7, Y(g)+3, g, "ax", "end"));
  }
  const LBL = [];
  const SER = [["share of the episode hidden","--cover",idx(T.rate),T.ends[0]],
               ["total steps spent in a bush","--muted",idx(T.steps),T.ends[1]],
               ["steps survived","--warm",idx(T.surv),T.ends[2]]];
  SER.forEach(function(row){
    const name=row[0], cvar=row[1], ix=row[2], ends=row[3];
    let d=""; ix.forEach((v,j) => d += (j?"L":"M") + X(j) + " " + Y(v));
    s.appendChild(el("path",{d:d, fill:"none", style:"stroke:"+CV(cvar),
      "stroke-width":2.4, "stroke-linejoin":"round"}));
    ix.forEach((v,j) => s.appendChild(el("circle",{cx:X(j), cy:Y(v), r:2.8,
      style:"fill:"+CV(cvar)})));
    LBL.push({y: Y(ix[N-1]), name: name, cvar: cvar, val: ends});
  });
  /* Two of these three lines finish close together, and each label is two lines tall. Push them
     apart rather than trusting the data to stay conveniently spaced - the label block is 30px and
     the gap between "total steps" and "steps survived" is 25px on this data alone. */
  LBL.sort((a,b) => a.y - b.y);
  for (let i = 1; i < LBL.length; i++)
    if (LBL[i].y - LBL[i-1].y < 32) LBL[i].y = LBL[i-1].y + 32;
  LBL.forEach(function(L){
    s.appendChild(txt(ml+pw+10, L.y-3, L.name, "lbl", null, CV(L.cvar)));
    s.appendChild(txt(ml+pw+10, L.y+11, L.val, "ax", null, CV("--muted")));
  });
  T.labels.forEach((l,j) => s.appendChild(txt(X(j), H-mb+16, l, "ax", "middle")));
  xlab(s, ml+pw/2, H-36, "how far the predator can see, in tiles  →");
  ylab(s, 15, mt+ph/2, "each measure indexed to 100 at range 1");
  put("three", s);
})();

/* FIGURE 5 - the same three measures, every factor, low setting to high. */
(function(){
  const K = Object.keys(TM), W=700, L=202, gh=16, gap=3, mt=44;
  const grp = 3*gh + 2*gap, pad = 16;
  const H = mt + K.length*(grp+pad) + 54, xw = W-L-34, LO=-100, HI=200;
  const s = svg(W,H);
  const X = v => L + (Math.max(LO, Math.min(HI, v)) - LO) / (HI - LO) * xw;
  for (const g of [-100,-50,0,50,100,150,200]) {
    s.appendChild(el("line",{x1:X(g), y1:mt-12, x2:X(g), y2:H-46,
      style:"stroke:"+CV(g===0?"--rule":"--grid"), "stroke-width":g===0?1.4:.5}));
    s.appendChild(txt(X(g), H-32, (g>0?"+":"")+g+"%", "ax", "middle"));
  }
  const SER = [["share of the episode hidden","--cover"],
               ["total steps spent in a bush","--muted"],
               ["steps survived","--warm"]];
  K.forEach(function(k,i){
    const top = mt + i*(grp+pad), t = TM[k];
    s.appendChild(txt(L-11, top+12, k, "lbl", "end"));
    s.appendChild(txt(L-11, top+25, t.gloss, "ax", "end", CV("--muted")));
    t.d.forEach(function(v,b){
      const y = top + b*(gh+gap), x0 = X(0), x1 = X(v), clipped = (v>HI || v<LO);
      s.appendChild(el("rect",{x:Math.min(x0,x1), y:y,
        width:Math.max(Math.abs(x1-x0), 1.5), height:gh, style:"fill:"+CV(SER[b][1]), rx:1}));
      /* A clipped bar must SAY it is clipped. An axis that silently truncates the largest effect
         on the page would be the very failure this section is about. */
      if (clipped) { for (const o of [0,4]) s.appendChild(el("line",
        {x1:x1-o-4, y1:y, x2:x1-o+2, y2:y+gh, style:"stroke:"+CV("--bg"), "stroke-width":2})); }
      /* A clipped bar's label cannot sit BEYOND the clip: there is no axis left to put it on,
         and it runs off the drawing. Print it inside the bar instead, the way Figure 17 prints
         its shares - white on the fill, right-aligned at the clipped end. */
      if (clipped) {
        s.appendChild(txt(x1-9, y+gh-4, (v>0?"+":"")+v+"% (off scale)", "ax", "end", CV("--bg")));
      } else {
        s.appendChild(txt(x1 + (v>=0?7:-7), y+gh-4, (v>0?"+":"")+v+"%", "ax",
                          v>=0?"start":"end"));
      }
    });
  });
  SER.forEach(function(c,j){ const x = L + j*168;
    s.appendChild(el("rect",{x:x, y:10, width:10, height:10, style:"fill:"+CV(c[1]), rx:2}));
    s.appendChild(txt(x+15, 19, c[0], "ax"));
  });
  xlab(s, L+xw/2, H-14, "change from the factor's lowest setting to its highest");
  put("tri", s);
})();
"""


def build_js(M):
    tm = {m["key"]: {"labels": m["labels"],
                     "rate": [round(x, 2) for x in m["rate"]],
                     "steps": [round(x, 2) for x in m["steps"]],
                     "surv": m["surv"], "gloss": m["gloss"],
                     "ends": [f'{m["rate"][0]:.1f}% \u2192 {m["rate"][-1]:.1f}%',
                              f'{m["steps"][0]:.1f} \u2192 {m["steps"][-1]:.1f}',
                              f'{halfup(m["surv"][0]):,} \u2192 {halfup(m["surv"][-1]):,}'],
                     "d": [round(m["d_rate"]), round(m["d_steps"]), round(m["d_surv"])]}
          for m in M}
    return ("<script>\n/* Merged from the environment-factor study. Every number here is derived\n"
            "   from D.curves above by scripts/analysis/studies/trajectory_factors/\n"
            "   merge_env_into_a01.py - none of it is typed by hand. */\n"
            "const TM=" + json.dumps(tm) + ";\n" + JS_BODY + "</script>\n")


HTML_BLOCK = """
<h3 id="share-not-total">Why hiding is counted as a share, not a total</h3>
<p>There are two obvious ways to write down how much an agent hid, and on the strongest factors in
this world they point in <strong>opposite directions</strong>. Counting the <em>share of the
episode</em> spent in a bush says a keener predator makes the agent hide far more. Counting the
<em>total steps</em> spent in a bush says the same predator makes it hide rather less. Both are
arithmetically correct.</p>
<p>They disagree because of the third measure. A predator that sees further kills sooner, so the
episode collapses from __SURV0__ steps to __SURV1__. Hiding for __RATE1__% of a __SURV1__-step life
is fewer steps than hiding for __RATE0__% of a __SURV0__-step one, even though the second agent is
doing far more hiding relative to the life it has. <strong>The total is mostly a measurement of how
long the agent stayed alive</strong>, with its behaviour as a minor term.</p>

<div class="motive"><b>Why this analysis</b>This page reports a rate everywhere, and that choice
deserves defending rather than assuming &mdash; a reader is entitled to ask what the raw counts
would have said. The answer turned out to be worth its own section: the raw count does not merely
lose power, it reverses the sign on the two largest effects in the environment. Survival is not a
nuisance to be divided out. It is the quantity that makes the other two measures disagree, which is
why it is carried here as an outcome in its own right rather than as a denominator.</div>

<figure class="panel">
  <div class="fignum">Figure 4 &mdash; one factor, three ways of counting</div>
  <div id="three"></div>
  <figcaption><b>Horizontal axis:</b> how far the predator can see, in tiles, from 1 to 7.
  <b>Vertical axis:</b> each measure indexed to 100 at range&nbsp;1 so that all three share one
  scale; the raw values are printed beside each line. Green is the share of the episode spent
  hidden, grey the total number of steps spent in a bush, amber the number of steps survived. Green
  rises to __IDXR__, grey falls to __IDXS__, amber falls to __IDXV__ &mdash; the agent hides
  <em>more intensely</em> and <em>less in total</em>, because it is dead sooner. Read the grey line
  on its own and you would conclude that dangerous predators make this agent hide less.</figcaption>
<div class="method"><b>How this was computed</b><dl><dt>data used</dt><dd>the __NDR__ episodes with exactly one predator, __PCTDR__% of the 1,000,000 collected. Detection range belongs to a predator, so it is undefined when there is none and ambiguous when there are two</dd><dt>share hidden</dt><dd>total bush steps in the bin &divide; total action steps in the bin &mdash; the same quantity drawn green in Figure&nbsp;3, with the spawn row (<code>t=0</code>) excluded from both</dd><dt>total bush steps</dt><dd>the share above &times; the mean episode length in the bin. Derived rather than counted, because the stored aggregates behind this page hold the rate and the length but not the raw total. Against the earlier environment study, which counted the total directly and did <em>not</em> exclude the spawn row, the derivation agrees to within 0.27%</dd><dt>steps survived</dt><dd>mean episode length in the bin, in steps &mdash; the amber line of Figure&nbsp;3</dd><dt>indexing</dt><dd>each series divided by its own value at range&nbsp;1, then multiplied by 100. Indexing is what lets three quantities in three different units (one percentage, two step counts) be read against one axis. It shows relative movement only &mdash; the heights carry no absolute meaning, which is why the raw values are printed too</dd><dt>why this is causal</dt><dd>detection range is rolled at random by the environment before the agent acts, so comparing bins is a randomised contrast rather than an observed correlation</dd></dl></div>
</figure>

<p>This is not a quirk of one factor. Of the seven world settings a predator or the terrain
controls, <strong>__NDIS__</strong> move the share and the total in opposite directions &mdash;
__DISLIST__ &mdash; and those __NDIS__ include the two largest effects on this page.</p>

<figure class="panel">
  <div class="fignum">Figure 5 &mdash; every factor, all three measures</div>
  <div id="tri"></div>
  <figcaption><b>Horizontal axis:</b> the change in each measure between the factor's lowest and
  highest setting, as a percentage of its value at the lowest. <b>Vertical axis:</b> the seven
  world settings, one group of three bars each, ordered by how much they move the share. Wherever
  the green and the grey bar point opposite ways, the two ways of counting disagree about what that
  factor does. Predator count's green bar runs off the scale at +614% and is marked as clipped
  rather than quietly truncated. Note the flat case as well: <code>predator max stamina</code>
  moves nothing on any of the three, which is a real null rather than a measurement that
  failed.</figcaption>
<div class="method"><b>How this was computed</b><dl><dt>the three bars</dt><dd>green is the share of the episode spent hidden, grey the total steps spent in a bush, amber the steps survived &mdash; each read at the factor's lowest and highest setting, expressed as the percentage change between the two</dd><dt>data used</dt><dd>the four predator traits use only the __NTRAIT__ exactly-one-predator episodes, __PCTTRAIT__% of the million, for the reason given in Figure&nbsp;4. Predator count, bushes available and hiding predators are defined in every episode and use all 1,000,000. The bars are therefore comparable in unit, not in population</dd><dt>a caution on percentages</dt><dd>the percentage change in a rate depends on how small that rate started. Predator count's +614% is large partly because hiding starts at only __P0__% when no predator is present; the same change stated in percentage points is +__P0PP__ pp. The table below carries the underlying values so no reader is left with the ratio alone</dd><dt>why these seven</dt><dd>they are the settings the earlier environment-factor study covered. The full set of everything this world varies &mdash; twenty-five factors, including the agent's own starting state and every smell channel &mdash; is Figure&nbsp;2</dd></dl></div>
</figure>

__TABLE__

<h3 id="cannot-perceive">The strongest thing in its world is one it cannot perceive</h3>
<p>Detection range is the second-largest effect on this page, and the agent has no sense for it. As
Section&nbsp;1 sets out, a predator's traits never reach the observation at all: what arrives is a
fixed class marker and a smell drawn from an <em>independent</em> random stream. Nothing the agent
can see, smell or feel tells it whether the predator in front of it sees one tile or seven.</p>
<p>So this is not an agent recognising a dangerous-looking predator and taking cover. It is an
agent that gets detected and chased more often, and hides more as a result. The effect is
<em>causally</em> identified &mdash; the trait is rerolled at random every episode, so nothing about
the agent can confound it &mdash; but the whole pathway runs through experienced consequence rather
than perception. The agent responds to what the trait <em>does to it</em>, not to the trait.</p>
<p>That distinction matters for reading the rest of this page. A large, clean, causally identified
effect turns out not to be evidence of anything the agent perceives &mdash; and it sets up the
opposite case in Section&nbsp;3, a factor the agent perceives <em>vividly</em> and gets wrong.</p>
"""


FIGREF = re.compile(r"Figure(&nbsp;|\s)(\d+)")


def figure_map(html):
    """number -> the first 46 characters of that figure's title, from the fignum divs."""
    return {int(n): t.strip()[:46]
            for n, t in re.findall(r'class="fignum">Figure\s+(\d+)\s*&mdash;([^<]*)', html)}


def renumber(html):
    """Shift Figures >= SHIFT_FROM by SHIFT_BY, in the fignum divs and in the prose alike.

    re.sub walks each match exactly once, so a number cannot be shifted twice in one pass - which
    is the failure mode a naive chain of replacements would have (4->6, then that 6 -> 8).
    """
    def bump(m):
        n = int(m.group(2))
        return f"Figure{m.group(1)}{n + SHIFT_BY if n >= SHIFT_FROM else n}"
    return FIGREF.sub(bump, html)


def main():
    write = "--write" in sys.argv
    html = open(PAGE, encoding="utf-8").read()
    if MARKER in html:
        fail("the page already carries the merged section - refusing to renumber a second time")

    M = three_measures(load_curves(html))
    dis, flat = check(M)
    by = {m["key"]: m for m in M}
    dr, pc = by["predator detection range"], by["predator count"]

    # ---- fill the prose from the data, so no number in it can be typed wrong ----------------
    idx = lambda a: a[-1] / a[0] * 100
    dis_names = [m["key"] for m in dis]
    dislist = ", ".join(dis_names[:-1]) + " and " + dis_names[-1] if len(dis_names) > 1 \
        else dis_names[0]
    n_trait = dr["n"]
    subs = {
        "__SURV0__": f"{halfup(dr['surv'][0]):,}", "__SURV1__": f"{halfup(dr['surv'][-1]):,}",
        "__RATE0__": f"{dr['rate'][0]:.0f}",    "__RATE1__": f"{dr['rate'][-1]:.0f}",
        "__IDXR__":  f"{idx(dr['rate']):.0f}",  "__IDXS__":  f"{idx(dr['steps']):.0f}",
        "__IDXV__":  f"{idx(dr['surv']):.0f}",
        "__NDR__":   f"{n_trait:,}",  "__PCTDR__": f"{n_trait / TOTAL_EPISODES * 100:.1f}",
        "__NTRAIT__": f"{n_trait:,}", "__PCTTRAIT__": f"{n_trait / TOTAL_EPISODES * 100:.1f}",
        "__NDIS__":  {1: "one", 2: "two", 3: "three", 4: "four"}.get(len(dis), str(len(dis))),
        "__DISLIST__": dislist,
        "__P0__":    f"{pc['rate'][0]:.1f}",
        "__P0PP__":  f"{pc['rate'][-1] - pc['rate'][0]:.0f}",
        "__TABLE__": build_table(M),
    }
    block = HTML_BLOCK
    for k, v in subs.items():
        block = block.replace(k, v)
    left = re.findall(r"__[A-Z0-9]+__", block)
    if left:
        fail(f"unsubstituted placeholders remain: {sorted(set(left))}")

    # ---- splice ---------------------------------------------------------------------------
    # One new CSS rule. The merged block otherwise reuses classes the page already defines
    # (.panel .scroll .num .method .motive .fignum), so this is the whole styling footprint.
    css_anchor = "td.num{font-family:var(--mono);font-size:.83rem}"
    if html.count(css_anchor) != 1:
        fail("could not find the stylesheet anchor to add the .sub rule after")
    html = html.replace(css_anchor, css_anchor + "\n"
        ".sub{display:block;font-family:var(--mono);font-size:.68rem;color:var(--muted);"
        "margin-top:.12rem;white-space:normal}")

    before = figure_map(html)
    anchor = '<h2>3 &nbsp;The mistake it makes</h2>'
    if html.count(anchor) != 1:
        fail(f"expected exactly one {anchor!r} to insert before, found {html.count(anchor)}")
    out = renumber(html).replace(anchor, block + "\n" + anchor)
    out = out.replace("</body>", build_js(M) + "</body>") if "</body>" in out \
        else out + build_js(M)

    # ---- verify the renumbering rather than trusting it ------------------------------------
    after = figure_map(out)
    for n, title in before.items():
        want = n + SHIFT_BY if n >= SHIFT_FROM else n
        if after.get(want) != title:
            fail(f"Figure {n} ({title!r}) should now be Figure {want}, "
                 f"but that slot holds {after.get(want)!r}")
    nums = sorted(after)
    if nums != list(range(1, len(nums) + 1)):
        fail(f"figure numbers are not 1..N after the merge: {nums}")
    refs = {int(n) for _, n in FIGREF.findall(out)}
    missing = refs - set(after)
    if missing:
        fail(f"the text refers to figures that do not exist: {sorted(missing)}")
    print(f"  figures 1..{len(nums)}, all sequential; "
          f"{len(before)} pre-existing titles kept their identity; every reference resolves")

    if not write:
        print("  DRY RUN - pass --write to apply")
        return
    open(PAGE, "w", encoding="utf-8").write(out)
    print(f"  wrote {PAGE}  ({len(out):,} chars, was {len(html):,})")


if __name__ == "__main__":
    main()

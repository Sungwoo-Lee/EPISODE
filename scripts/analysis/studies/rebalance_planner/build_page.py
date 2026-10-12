"""Assemble the 'Hide or Forage Balance' page: house chrome + script-drawn figures + script-emitted tables.

Follows scripts/analysis/studies/internal_state_interactions/build_page.py. The builder EMBEDS, it never draws
(guide 2.7). It fails rather than shipping a partial page: a figure with no generating script, a missing
raster / vector / data statement / kind tag, a caption with no axes sentence, a figure with no method block or
one that never says what the figure does not show, vector art inside a <figure>, figure numbers out of
document order, a table outside a scroll box, a <title> that differs from the <h1>, a failed validation, or any
unsubstituted token. Every number the prose quotes is a {{token}} computed here from the study's JSON
(register F15), and the summary callout is read from summary_note.html beside the template so its wording
can be edited without touching this file.

  python build_page.py
"""
import base64, json, os, re, sys

import numpy as np

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPTS, "..", "..", "..", ".."))
HOUSE = os.path.join(ROOT, "docs/develop/active/meta/house_style_sheet.html")     # the BUILT sheet (font inlined)
HERE = os.path.join(ROOT, "docs/experiments/active/rebalance_planner")
TPL = os.path.join(HERE, "hide_or_forage_balance.template.html")
NOTE = os.path.join(HERE, "summary_note.html")
OUT = os.path.join(HERE, "hide_or_forage_balance.html")
FIGS = os.path.join(HERE, "figures")
sys.path.insert(0, SCRIPTS)
import _common as CC                                                            # noqa: E402
import _deaths as Dd                                                            # noqa: E402

fail = []


def die():
    if fail:
        for f in fail:
            print("  BUILD FAILURE:", f)
        sys.exit(1)


def J(name):
    return json.load(open(os.path.join(FIGS, name)))


# --- validation gates ------------------------------------------------------------------------------
vb, vp = J("validation_body.json"), J("validation_planner.json")
if not vb.get("pass_"):
    fail.append("validation_body.json did not pass")
if not vp.get("pass_"):
    fail.append("validation_planner.json did not pass")
R = J("results.json"); W = R["worlds"]; MAPF = J("mappings.json"); MAP = MAPF["worlds"]
if "A+ predator count exactly 1" not in R.get("revision", ""):
    fail.append("results.json predates the A+ = exactly one predator revision")
die()

# --- numbers quoted in the prose, all computed here -------------------------------------------------
p0 = lambda x: f"{100 * x:.0f}"
MAIN = [f"w{k}" for k in range(1, 9)]
dec = lambda t, d: W[t]["decision_open"][d]
hun = lambda t: W[t]["exploratory_decision_open_hungry"]["forage"]
td = lambda t, d: W[t]["decision_open_ties_dropped"][d]
GN = np.linspace(0, 200, 51)
hungry_frac = float((GN < 100).mean())
N = {}
N["hide_min"], N["hide_max"] = p0(min(dec(t, "hide") for t in MAIN)), p0(max(dec(t, "hide") for t in MAIN))
N["eat_min"], N["eat_max"] = p0(min(dec(t, "forage") for t in MAIN)), p0(max(dec(t, "forage") for t in MAIN))
N["l05_hide"], N["l05_eat"] = p0(dec("level05", "hide")), p0(dec("level05", "forage"))
N["w4_eat"], N["w4_hide"], N["w4t4_eat"] = p0(dec("w4", "forage")), p0(dec("w4", "hide")), p0(dec("w4_trip4", "forage"))
N["hungry_frac"] = p0(hungry_frac)
_GT = np.linspace(-15, 15, 61)
N["n_starts"] = f"{51 * 26 * int(((_GT >= -10 - 1e-9) & (_GT <= 5 + 1e-9)).sum()):,}"     # planner grid, start range
N["eF_B_abs"] = f'{abs(100 * R["main_effects"]["forage share (open ground)"]["B"]):.1f}'
# "eating is best in about 0 % of start states above the setpoint": main-world eat share over all states
# minus hungry share x hungry fraction = eat share among fed states
fed_eat = max((dec(t, "forage") - hun(t) * hungry_frac) / (1 - hungry_frac) for t in MAIN)
if fed_eat > 0.01:
    fail.append(f"the page says eating is best in about 0 % of fed start states, but one world has {fed_eat:.1%}")
N["bar_hungry"] = f"{100 * 0.20 / hungry_frac:.0f}"
for t in ["level05", "w2", "w3", "w4", "w7", "w8"]:
    N[f"{t}_hun"] = p0(hun(t))
N["w4t4_hun"] = p0(hun("w4_trip4"))
nt = [W[t]["gap_within_1"] for t in MAIN]
N["nt_min"], N["nt_max"] = p0(min(nt)), p0(max(nt))
sv = {t: W[t]["survival"] for t in MAIN}
N["surv_min"], N["surv_min_w"] = p0(min(sv.values())), min(sv, key=sv.get)[1]
N["surv_max"], N["surv_max_w"] = p0(max(sv.values())), max(sv, key=sv.get)[1]
N["l05_surv"], N["w1_surv"] = p0(W["level05"]["survival"]), p0(W["w1"]["survival"])
N["starv_early"] = p0(max(W[t]["death_share_of_starts"]["starvation"] for t in MAIN))
E = R["main_effects"]; pp = lambda k, g: f"{100 * E[k][g]:+.1f}"
for g in "ABCD":
    N[f"eA_{g}"] = pp("hide share (open ground)", g); N[f"eF_{g}"] = pp("forage share (open ground)", g)
    N[f"eS_{g}"] = pp("survival at 500 steps", g); N[f"eT_{g}"] = pp("time eating", g); N[f"eB_{g}"] = pp("time in bush", g)
for t in ["w8_heal5", "w4_heal5", "w4_heal12.5", "w8_g0.99", "w4_g0.99", "w8_trip8", "w8_pred0.5", "w8_pred2"]:
    k = t.replace(".", "")
    N[f"{k}_hide"], N[f"{k}_eat"] = p0(dec(t, "hide")), p0(dec(t, "forage"))
    N[f"{k}_tdhide"], N[f"{k}_tdeat"] = p0(td(t, "hide")), p0(td(t, "forage"))
    N[f"{k}_surv"] = p0(W[t]["survival"])
N["w8_surv"], N["w4_surv"] = p0(W["w8"]["survival"]), p0(W["w4"]["survival"])
both = [t for t, w in W.items() if w.get("role") == "lever" and w["decision_open"]["hide"] >= .2 and w["decision_open"]["forage"] >= .2]
N["lever_both"] = ", ".join(both) if both else "none"
if both != ["w4_heal5"]:
    fail.append(f"the page says only world 4 + bush healing 5 has both >= 20 % among levers; found {both}")
N["w4_time_bush"], N["w4_time_travel"] = p0(W["w4"]["time_share"]["bush"]), p0(W["w4"]["time_share"]["travel"])
bmin = min(W[t]["time_share"]["bush"] for t in MAIN); bmax = max(W[t]["time_share"]["bush"] for t in MAIN)
N["tbush_min"], N["tbush_max"] = p0(bmin), p0(bmax)
sA = sorted({round(MAP[t]["predator_scale"], 2) for t in MAIN})
N["scaleAp"], N["scaleAm"] = f"{sA[0]:.2f}", f"{sA[-1]:.2f}"
lam = MAPF["lam_by_sight_pounce"]
N["lam33"] = f'{1000 * lam["3,3"]["lam"]:.1f}'
N["lamAp"] = f'{1000 * np.mean([lam[f"{d},{r}"]["lam"] for d in (2, 3) for r in (2, 3)]):.1f}'
N["lam05"] = f'{1000 * np.mean([lam[f"{d},{r}"]["lam"] for d in range(1, 8) for r in (2, 3)]):.1f}'
N["lam32"], N["lam22"] = f'{1000 * lam["3,2"]["lam"]:.1f}', f'{1000 * lam["2,2"]["lam"]:.1f}'
mr = MAPF["measured_rates_level05"]
N["p_pred_move"] = f'{mr["move"]["pred"]:.4f}'
N["trap_slope"] = f'{MAPF["trap_slope_per_trap"] * 1e5:.1f}'
N["trip14"] = f'{MAPF["food_trip_monte_carlo"]["(1, 4)"]["median"]:.0f}'
N["trip13"] = f'{MAPF["food_trip_monte_carlo"]["(1, 3)"]["median"]:.0f}'
N["trapinv_min"] = f'{100 * min(MAP[t]["hazard"]["move"]["trap"]["p"] for t in MAIN if not MAP[t]["settings"]["visible"]):.1f}'
N["trapinv_max"] = f'{100 * max(MAP[t]["hazard"]["move"]["trap"]["p"] for t in MAIN if not MAP[t]["settings"]["visible"]):.1f}'
N["trapvis"] = f'{100 * MAP["w1"]["hazard"]["move"]["trap"]["p"]:.1f}'
N["pq_eps"] = f'{MAPF["parquet"]["episodes"]:,}'
N["outside_share"] = f'{MAPF["outside_share_used"]:.2f}'
osb = MAPF["outside_share_by_store"].values()
N["outside_lo"], N["outside_hi"] = f"{min(osb):.2f}", f"{max(osb):.2f}"
# validation
N["vb_max"] = f'{max(max(s["max_abs_diff"].values()) for s in vb["sets"]):.0e}'
N["vb_n"] = f'{vb["n"]:,}'; N["vb_sets"] = str(len(vb["sets"]))
r2 = vp["2_rollout_equals_old"]
N["vp_v"] = f'{max(m["max_abs_V_diff"] for m in vp["1_plugin_equals_old"]):.1g}'
l3 = vp["3_level05_decomposed_vs_old"]["warm0"]
N["v3_new"], N["v3_old"] = p0(l3["new_survival"]), p0(l3["old_survival"])
N["v3_newhide"], N["v3_oldhide"] = p0(l3["new_decision"]["hide"]), p0(l3["old_balance"]["rest in cover"])
# Section A
D = Dd.deaths(); L = Dd.by_level()
s05 = "basicq2_w2/rppo_bq2cover_lvl05_t1none_s42"
for k, key in (("a_surv", "max_steps"), ("a_starv", "starvation"), ("a_inj", "injury")):
    N[k] = p0(D[s05]["reasons"].get(key, 0) / D[s05]["episodes"])
f = {a: sum(D[s]["fatal"][k][a] for s in L["05"] for k in ("visible", "both")) for a in Dd.STATES}
st = {a: sum(D[s]["steps"][a] for s in L["05"]) for a in Dd.STATES}
N["a_ate_share"] = p0(f["out_ate20"] / sum(f.values()))
N["a_ate_steps"] = p0(st["out_ate20"] / sum(st.values()))
N["a_rate_ate"] = f'{1000 * f["out_ate20"] / st["out_ate20"]:.1f}'
N["a_rate_tow"] = f'{1000 * f["out_toward"] / st["out_toward"]:.1f}'
N["a_rate_oth"] = f'{1000 * f["out_other"] / st["out_other"]:.1f}'
inj = sum(D[s]["fatal"]["injury_deaths"] for s in L["05"])
N["a_pred_of_inj"] = p0(sum(f.values()) / inj)
fat = np.sum([np.array(D[s]["fatal"]["pred_sat_hist"], float) for s in Dd.L05_STORES], 0)
allo = np.sum([np.array(D[s]["sat_all_out"], float) for s in Dd.L05_STORES], 0)
N["a_fat20"], N["a_all20"] = p0(fat[:4].sum() / fat.sum()), p0(allo[:4].sum() / allo.sum())
B = Dd.counts(); agg = {}
for s in L["05"]:
    for k, n in B[s].items():
        k = int(k); a = agg.setdefault(k // 10000, [0, 0]); a[1] += n; a[0] += n * (k % 100 == 1)
for c in (0, 1, 2):
    N[f"a_cnt{c}"] = p0(agg[c][0] / agg[c][1])
a02 = [0, 0]
for s_ in L["02"]:
    for k, n in B[s_].items():
        k = int(k); a02[1] += n; a02[0] += n * (k % 100 == 1)
N["a_l02"] = f"{100 * a02[0] / a02[1]:.0f}"
A1 = J("data/one_predator_l05_by_sight_pounce.json"); cell = {}
for r in A1["rows"]:
    c = cell.setdefault((r["sight"], r["pounce"]), [0, 0]); c[0] += r["endings"].get("1", 0); c[1] += r["episodes"]
N["a_s33"], N["a_s32"] = p0(cell[(3, 3)][0] / cell[(3, 3)][1]), p0(cell[(3, 2)][0] / cell[(3, 2)][1])
N["a_s1"] = p0((cell[(1, 2)][0] + cell[(1, 3)][0]) / (cell[(1, 2)][1] + cell[(1, 3)][1]))

# --- house chrome --------------------------------------------------------------------------------
house = open(HOUSE).read()
style = re.search(r"<style>.*?</style>", house, re.S)
script = re.search(r"<script>.*?</script>", house, re.S)
viewer = re.search(r'<div class="lb fit" id="lb".*?\n</div>', house, re.S)
if not (style and script and viewer):
    fail.append("could not lift the house <style>, viewer markup and <script> from the built sheet"); die()
page = open(TPL).read()
page = page.replace("__HOUSE_STYLE__", style.group(0))
assert page.count("__HOUSE_SCRIPT__") == 1
page = page.replace("__HOUSE_SCRIPT__", viewer.group(0) + "\n" + script.group(0))
page = page.replace("__SUMMARY__", open(NOTE).read())

# --- numbers -------------------------------------------------------------------------------------
for k, v in N.items():
    page = page.replace("{{" + k + "}}", str(v))

# --- data-accounting blocks (guide 11b), kind badges, tables -------------------------------------
stems = sorted(set(re.findall(r'data-fig="([^"]+)"', page)))
for stem in stems:
    df = os.path.join(FIGS, f"{stem}.data.txt")
    if not os.path.exists(df):
        fail.append(f"{stem}: no {stem}.data.txt"); continue
    rows = [l.rstrip("\n").split("|") for l in open(df) if l.strip()]
    cells = "".join(f'<tr><td>{w}</td><td class="n">{u}</td><td class="n">{t}</td><td class="n">{p}%</td><td>{n}</td></tr>'
                    for w, u, t, p, n in rows)
    for w, u, t, p_, n in rows:
        if float(p_) < 100.0 and not n.strip():
            fail.append(f"{stem}: data row '{w}' uses {p_} % with no reason (F71)")
    shares = [float(r[3]) for r in rows]
    span = "100 %" if min(shares) == 100.0 else (f"{min(shares):.1f} %" if min(shares) == max(shares)
                                                 else f"{min(shares):.1f}&ndash;{max(shares):.1f} %")
    summ = (f'<b>Data.</b> {len(rows)} subset{"s" if len(rows) > 1 else ""}, each using {span} of what was '
            f'available &mdash; open for the counts, emitted by the figure&rsquo;s own script')
    block = (f'<details class="datause"><summary>{summ}</summary>'
             '<p class="cue" hidden>Wider than this column — scroll sideways; the right-hand columns are cut off.</p>'
             '<div class="scroll"><table class="datatable"><thead><tr><th>subset</th>'
             '<th class="n">used</th><th class="n">available</th><th class="n">share</th>'
             f'<th>why</th></tr></thead><tbody>{cells}</tbody></table></div>'
             f'<p class="prov">Drawn by <code>scripts/<wbr>analysis/<wbr>studies/<wbr>rebalance_planner/<wbr>{stem}.py</code>⁠, '
             f'which also writes <code>figures/<wbr>{stem}.data.txt</code>⁠ — the table above.</p></details>')
    page = page.replace(f"__DATA:{stem}__", block)
    kf = os.path.join(FIGS, f"{stem}.kind.txt")
    if not os.path.exists(kf):
        fail.append(f"{stem}: no kind tag"); continue
    k = open(kf).read().strip()
    page = page.replace(f"__KIND:{stem}__", f'<p class="kind kind-{k}">{CC.KIND[k]}</p>')
for m in set(re.findall(r"__TABLE:([a-z0-9_]+)__", page)):
    tf = os.path.join(FIGS, f"{m}.html")
    if not os.path.exists(tf):
        fail.append(f"table fragment {m}.html missing - run tables.py"); continue
    page = page.replace(f"__TABLE:{m}__", open(tf).read())

# --- embed rasters by key ------------------------------------------------------------------------
for stem in stems:
    png = os.path.join(FIGS, f"{stem}.png")
    if not os.path.exists(png):
        fail.append(f"{stem}: {stem}.png missing"); continue
    if not os.path.exists(os.path.join(SCRIPTS, f"{stem}.py")):
        fail.append(f"{stem}: no generating script {stem}.py")
    for ext in ("svg", "pdf"):
        if not os.path.exists(os.path.join(FIGS, f"{stem}.{ext}")):
            fail.append(f"{stem}: no {ext} companion")
    b64 = base64.b64encode(open(png, "rb").read()).decode()
    page = re.sub(rf'(<img data-fig="{re.escape(stem)}")', rf'\1 src="data:image/png;base64,{b64}"', page, count=1)

# --- per-figure checks, element by element -------------------------------------------------------
nums, words = [], {}
for m in re.finditer(r"<figure>.*?</figure>", page, re.S):
    blk = m.group(0); flat = re.sub(r"\s+", " ", blk)
    sm = re.search(r'data-fig="([^"]+)"', blk); stem = sm.group(1) if sm else "<no data-fig>"
    for need, why in (('src="data:image/png;base64,', "raster never embedded"), ("<b>Axes.</b>", "no Axes sentence (11a)"),
                      ("<b>Data.</b>", "no data block (11b)"), ("<b>How it is computed.</b>", "no method block (11c)"),
                      ('class="kind kind-', "no kind badge"), ("zoomhint", "no click-to-open hint (2.6)")):
        if need not in flat:
            fail.append(f"{stem}: {why}")
    if "does not show" not in flat:
        fail.append(f"{stem}: method block never says what the figure does NOT show")
    if re.search(r"<(svg|canvas)\b", blk):
        fail.append(f"{stem}: vector art drawn in the page (2.7)")
    alt = re.search(r'alt="([^"]*)"', blk)
    if not alt or len(alt.group(1)) < 60:
        fail.append(f"{stem}: alt text missing or short")
    hm = re.search(r"<b>How it is computed\.</b>(.*?)</span>", flat)
    if hm:
        n = len(re.sub(r"<[^>]+>", " ", hm.group(1)).split()); words[stem] = n
        if not 150 <= n <= 260:
            fail.append(f"{stem}: 'How it is computed' is {n} words (target 150-250, 11c)")
    fn = re.search(r"<b>Figure (\d+)", flat)
    if not fn:
        fail.append(f"{stem}: no 'Figure N'")
    else:
        nums.append(int(fn.group(1)))
if nums != list(range(1, len(nums) + 1)):
    fail.append(f"figure numbers not 1..N in document order: {nums}")
for tm in re.finditer(r"<table[^>]*>", page):
    before = page[max(0, tm.start() - 400):tm.start()]
    if 'class="scroll"' not in before or '<p class="cue"' not in before:
        fail.append(f"a <table> lacks its scroll box or cue: {tm.group(0)[:60]}")
_tm = re.search(r"<title>(.*?)</title>", page); _hm = re.search(r"<h1>(.*?)</h1>", page)
if not (_tm and _hm and _tm.group(1).strip() == _hm.group(1).strip()):
    fail.append("<title> does not match <h1>")
if page.count("<section") != page.count("</section>"):
    fail.append("unbalanced <section>")
for phrase in ("survival-optimal", "more predator threat", "passes in hungry", "no lever can", "mostly hides"):
    if phrase in page.lower():
        fail.append(f"wording the verdict review ruled out is on the page: '{phrase}'")
left = re.findall(r"__[A-Z][A-Z0-9_:]*__|\{\{[^}]+\}\}", page)
if left:
    fail.append(f"unsubstituted tokens remain: {sorted(set(left))[:8]}")
if "data:font" not in page:
    fail.append("no embedded font")
die()
page = '<meta charset="utf-8">\n' + page
open(OUT, "w").write(page)
print(f"wrote {os.path.relpath(OUT, ROOT)}  ({len(page) / 1e6:.2f} MB, {len(nums)} figures)")
print("method-block words:", words)

"""HTML table fragments for the 'Hide or Forage Balance' page, emitted from the study's JSON (never typed).

  t_groups       the four groups of settings, now (-) and new (+)            (mappings.py LEVELS)
  t_worlds       the eight worlds and the numbers the planner was given       (mappings.json)
  t_decision     per world: decision shares and near-ties (results.json; placed with Figure 6)
  t_outcomes     per world: survival and deaths (results.json; placed with Figure 8)
  t_time         per world: time use (results.json; placed with Figure 9)
  t_effects      group main effects                                          (results.json)
  t_sensitivity  sensitivity checks: food trip 4, discount 0.99              (results.json)
  t_levers       exploratory single-lever sweeps from worlds 8 and 4         (results.json)
Each fragment carries its own overflow cue and scroll box (house pattern). Written to figures/<name>.html.

  python tables.py
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C
import mappings as M

R = json.load(open(os.path.join(C.FIG, "results.json")))
W = R["worlds"]; MAP = json.load(open(os.path.join(C.FIG, "mappings.json")))["worlds"]
ORDER = ["level05"] + [f"w{k}" for k in range(1, 9)]
pc = lambda x, d=0: f"{100 * x:.{d}f}"


def label(t):
    if t == "level05":
        return "level 05"
    base = t.split("_")[0]
    return f"world {base[1]}"


def table(name, head, rows, cls="datatable ctab", numeric_from=1):
    th = "".join(f'<th class="n">{h}</th>' if i >= numeric_from else f"<th>{h}</th>" for i, h in enumerate(head))
    body = "".join("<tr>" + "".join(f'<td class="n">{c}</td>' if i >= numeric_from else f"<td>{c}</td>"
                                    for i, c in enumerate(r)) + "</tr>" for r in rows)
    html = ('<p class="cue" hidden>Wider than this column — scroll sideways; the right-hand columns are cut off.</p>'
            f'<div class="scroll"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>')
    open(os.path.join(C.FIG, f"{name}.html"), "w").write(html)
    print(f"  wrote {name}.html ({len(rows)} rows)")


# ---- groups --------------------------------------------------------------------------------------
L = M.LEVELS
rng = lambda a: f"{a[0]}–{a[1]}" if a[0] != a[1] else f"exactly {a[0]}"
lst = lambda v: f"{v[0]}" if len(v) == 1 else f"{v[0]}–{v[-1]}"
table("t_groups", ["group", "setting", "now (−)", "new (+)"], [
    ["A predator", "predator sight (<code>detection_range</code>, cells)", lst(L["A"]["-"]["sight"]), lst(L["A"]["+"]["sight"])],
    ["A predator", "pounce reach (<code>attack_range</code>, cells)", lst(L["A"]["-"]["pounce"]), lst(L["A"]["+"]["pounce"])],
    ["A predator", "predators per episode", rng(L["A"]["-"]["pred_count"]), rng(L["A"]["+"]["pred_count"])],
    ["B food", "food items per episode", rng(L["B"]["-"]["food_count"]), rng(L["B"]["+"]["food_count"])],
    ["B food", "bites per item (<code>max_consumption</code>)", L["B"]["-"]["bites"], L["B"]["+"]["bites"]],
    ["B food", "food energy per bite (<code>food_nutrition_gain</code>)", f'{L["B"]["-"]["gross"]:g}', f'{L["B"]["+"]["gross"]:g}'],
    ["B food", "net gain per eating step (bite − eating cost 1 − step cost 1)", f'+{L["B"]["-"]["gross"] - 2:g}', f'+{L["B"]["+"]["gross"] - 2:g}'],
    ["C concealment", "traps and rocks seen by the agent", "visible", "invisible (<code>visual_mask: all</code>)"],
    ["D hazard load", "rocks per episode", rng(L["D"]["-"]["rocks"]), rng(L["D"]["+"]["rocks"])],
    ["D hazard load", "traps (<code>hiding_predator</code>) per episode", rng(L["D"]["-"]["traps"]), rng(L["D"]["+"]["traps"])],
    ["D hazard load", "trap damage per hit", rng(tuple(int(x) for x in L["D"]["-"]["trap_dmg"])), rng(tuple(int(x) for x in L["D"]["+"]["trap_dmg"]))],
], cls="datatable ctab groups", numeric_from=99)

# ---- worlds and planner inputs -------------------------------------------------------------------
rows = []
for t in ORDER:
    m = MAP[t]; s = m["settings"]; hz = m["hazard"]["move"]
    rows.append([label(t), " ".join(s["signs"]) if s["signs"] else "—", f'{m["predator_scale"]:.2f}', m["food"]["trip"],
                 f'{m["food"]["per_item_net_of_drain"]:.0f}', f'{100 * hz["trap"]["p"]:.1f}', f'{100 * hz["rock"]["p"]:.1f}',
                 f'{m["mean_damage_per_step"]["move"]:.2f}'])
table("t_worlds", ["world", "A B C D", "predator odds (× level 05)", "food trip (steps)",
                   "energy per item", "trap hits / 100 steps", "rock hits / 100 steps",
                   "injury per step"], rows)

# ---- results: decisions (with Figure 6) and outcomes (with Figures 8-9) -----------------------------
rows, rows2 = [], []
for t in ORDER:
    w = W[t]; d = w["decision_open"]; td = w["decision_open_ties_dropped"]; ds = w["death_share_of_starts"]; ts = w["time_share"]
    rows.append([label(t), pc(d["hide"]), pc(d["forage"]), pc(d["other"]), "yes" if w["real_choice"] else "no",
                 f'{pc(td["hide"])} / {pc(td["forage"])}', pc(w["gap_within_1"])])
    rows2.append([label(t), pc(w["survival"]), pc(ds["predator"]), pc(ds["trap"]), pc(ds["starvation"]),
                  pc(ts["bush"]), pc(ts["travel"]), pc(ts["eat"]), pc(ts["warm"]), pc(ts["open"])])
table("t_decision", ["world", "hide best", "eat best", "other best", "real choice", "ties dropped: hide / eat",
                     "near-tie"], rows)
table("t_outcomes", ["world", "survived", "died: predator", "died: trap", "died: starving"], [r[:5] for r in rows2])
table("t_time", ["world", "in a bush", "travelling", "eating", "warming", "in the open"], [[r[0]] + r[5:] for r in rows2])

# ---- main effects --------------------------------------------------------------------------------
E = R["main_effects"]
names = {"A": "A predator", "B": "B food", "C": "C concealment", "D": "D hazard load"}
mets = [("hide share (open ground)", "hide best"), ("forage share (open ground)", "eat best"),
        ("survival at 500 steps", "survival"), ("injury deaths (share of starts)", "injury deaths"),
        ("time in bush", "time in bush"), ("time eating", "time eating")]
table("t_effects", ["group"] + [n for _, n in mets],
      [[names[g]] + [f"{100 * E[k][g]:+.1f}" for k, _ in mets] for g in "ABCD"])

# ---- sensitivity ---------------------------------------------------------------------------------
rows = []
for base, alt, what in [("w3", "w3_trip4", "trip to food 4 instead of 5"), ("w4", "w4_trip4", "trip to food 4 instead of 5"),
                        ("w7", "w7_trip4", "trip to food 4 instead of 5"), ("w8", "w8_trip4", "trip to food 4 instead of 5"),
                        ("w4", "w4_g0.99", "discount 0.99 instead of 0.95"), ("w8", "w8_g0.99", "discount 0.99 instead of 0.95")]:
    a, b = W[base], W[alt]
    rows.append([label(base), what, f'{pc(a["decision_open"]["hide"])} → {pc(b["decision_open"]["hide"])}',
                 f'{pc(a["decision_open"]["forage"])} → {pc(b["decision_open"]["forage"])}',
                 f'{pc(b["decision_open_ties_dropped"]["hide"])} / {pc(b["decision_open_ties_dropped"]["forage"])}',
                 f'{pc(a["survival"])} → {pc(b["survival"])}'])
table("t_sensitivity", ["world", "change", "hide best", "eat best", "ties dropped: hide / eat",
                        "survived"], rows, numeric_from=2)

# ---- levers ---------------------------------------------------------------------------------------
LV = [("", "as designed"), ("_pred0.5", "predator hit odds ×0.5"), ("_pred2", "predator hit odds ×2"),
      ("_trip4", "trip to food 4"), ("_trip6", "trip to food 6"), ("_trip8", "trip to food 8"),
      ("_heal12.5", "bush healing 12.5 (planner only)"), ("_heal5", "bush healing 5 (planner only)")]
rows = []
for base in ("w8", "w4"):
    for suf, nm in LV:
        w = W[base + suf]; d = w["decision_open"]; td = w["decision_open_ties_dropped"]; h = w["exploratory_decision_open_hungry"]
        rows.append([f"world {base[1]}: {nm}", pc(d["hide"]), pc(d["forage"]), pc(d["other"]),
                     f'{pc(td["hide"])} / {pc(td["forage"])}', pc(h["forage"]), pc(w["survival"])])
table("t_levers", ["start world and lever", "hide best", "eat best", "other best",
                   "ties dropped: hide / eat", "eat best, hungry only", "survived"], rows, cls="datatable ctab levers")

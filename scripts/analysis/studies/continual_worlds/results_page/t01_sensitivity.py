"""TABLE t01 — How the main study's verdict moves with the way per-switch votes are combined and with which
worlds count in the forgetting vote (CONTINUAL_WORLDS.md 10.8-10.9). A table, not a figure: writes the HTML
fragment figures/t01_sensitivity.html, substituted into the page as __TABLE:t01_sensitivity__.

Sources (read): tmp/20260929_cw_main_verdict.json 'sensitivity' (rules R1-R6: per-sequence signs of the four
measures, count favourable, beyond-noise measures, whether the sequence meets the per-sequence criterion,
overall verdict) and tmp/20260930_cw_sensitivity_extra.json (R7, R8, added after the verdict review).
For R7 'meets' is read from the file; the overall verdict is 'support' when at least 2 of the 3 sequences
meet (section 2). R8 differs from R1 only in its recovery sign (the file lists the changed switches), so a
sequence meets under R8 when it has >= 3 favourable measures and one of R1's beyond-noise measures is still
favourable -- the same criterion, applied to R8's signs.
"""
import os, sys, html; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

STEM = "t01_sensitivity"
V = C.load(C.VERDICT)["sensitivity"]
X = C.load(C.SENS_EXTRA)
SEQS = ("P1", "P2", "P3")
MEAS = ("dip", "rec", "ret", "forget")
G = {"fav": "+", "+": "+", "unfav": "−", "-": "−"}           # anything else: not favourable either way

# plain-language description, forgetting entry set, registered-literal?  (text, not numbers)
DESC = {"R1": ("net tally of counted votes; ties as registered", "Forage counted", "primary reading"),
        "R2": ("as R1, but recovery ties only on exact equality (the read-out's old bug)", "Forage counted", "not registered-literal"),
        "R3": ("a measure is favourable only if no counted vote goes against it", "Forage counted", "stricter than registered"),
        "R4": ("second visits only", "alternating worlds only", "the predicted shape, not the rule"),
        "R5": ("sum of the signed differences across the sequence", "Forage counted", "registered-consistent"),
        "R6": ("as R1", "alternating worlds only", "registered-consistent"),
        "R7": ("as R5", "alternating worlds only", "registered-consistent (added after review)"),
        "R8": ("as R1, and a recovery gap under one logging interval is also a tie", "Forage counted", "registered-consistent (added after review)")}

rules = {}
for k, v in V.items():
    rid = k.split()[0]
    assert rid in DESC, k
    per = {s: dict(signs=[G.get(v["per"][s]["signs"][m], "0") for m in MEAS], n=v["per"][s]["n_fav"],
                   meets=v["per"][s]["supports"]) for s in SEQS}
    for s in SEQS:
        assert per[s]["signs"].count("+") == per[s]["n"], (rid, s)
    rules[rid] = dict(per=per, overall=v["overall"])
for rid in ("R7", "R8"):
    per = {}
    for s in SEQS:
        e = X[s][rid]
        signs = [G.get(e["signs"][m], "0") for m in MEAS]
        assert signs.count("+") == e["n_fav"], (rid, s)
        if rid == "R7":
            meets = e["meets"]
        else:
            bn1 = V[next(k for k in V if k.startswith("R1"))]["per"][s]["beyond_noise_in"]
            meets = e["n_fav"] >= 3 and any(signs[MEAS.index(m)] == "+" for m in bn1)
        per[s] = dict(signs=signs, n=e["n_fav"], meets=meets)
    rules[rid] = dict(per=per, overall="SUPPORT" if sum(p["meets"] for p in per.values()) >= 2 else "NOT SUPPORTED")
# the R1 verdict under the registered rule must agree with 10.8
assert rules["R1"]["overall"] == "SUPPORT"
for rid in rules:
    n_meet = sum(p["meets"] for p in rules[rid]["per"].values())
    assert (rules[rid]["overall"] == "SUPPORT") == (n_meet >= 2), (rid, n_meet)

rows = []
for rid in sorted(rules, key=lambda r: int(r[1:])):
    d, fset, status = DESC[rid]
    cells = "".join(
        f'<td class="n">{" ".join(p["signs"])}<br><span class="meets">{"meets" if p["meets"] else "no"}</span></td>'
        for p in (rules[rid]["per"][s] for s in SEQS))
    ov = "support" if rules[rid]["overall"] == "SUPPORT" else "not supported"
    cls = ' class="pick"' if rid == "R1" else ""
    rows.append(f'<tr{cls}><td>{rid}</td><td>{html.escape(d)}<br><b>forgetting:</b> {fset}'
                f'<br><span class="status">{status}</span></td>{cells}<td>{ov}</td></tr>')
frag = ('<p class="cue" hidden>Wider than the screen — scroll sideways; the right-hand columns are cut off.</p>'
        '<div class="scroll"><table class="senstable"><thead><tr><th>rule</th><th>how votes combine</th>'
        '<th class="n">P1</th><th class="n">P2</th><th class="n">P3</th>'
        '<th>verdict</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>')
os.makedirs(C.FIG, exist_ok=True)
open(os.path.join(C.FIG, f"{STEM}.html"), "w").write(frag)
with_f = [r for r in rules if DESC[r][1] == "Forage counted" and r in ("R1", "R5")]
without_f = [r for r in rules if DESC[r][1] == "alternating worlds only" and r in ("R6", "R7")]
C.record_numbers(STEM, {
    "n_rules": str(len(rules)),
    "n_support": str(sum(r["overall"] == "SUPPORT" for r in rules.values())),
    "with_forage_support": " and ".join(r for r in with_f if rules[r]["overall"] == "SUPPORT"),
    "without_forage_support": str(sum(rules[r]["overall"] == "SUPPORT" for r in without_f)),
    "p1_ab_forget_sum": C.fmt(X["P1"]["R7"]["forget_AB_sum"], sign=True)})
print(f"  wrote {STEM}.html ({len(rules)} rules)")

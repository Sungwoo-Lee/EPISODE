"""Apply the pre-registered balance criteria (STUDY_PLAN.md Revisions 2, 2a, 2b) to every world of the
balance sweep, per map; the primary verdict is the map without a warm bush ("warm0").

  1 time      no activity > 70 % of steps; cover, warm cell, eating each >= 10 %
  2 drive     eating ratio >= 2, hiding ratio >= 2, per-decision warming ratio (b') >= 2
  3 death     if >= 5 % of starts die after step 20: no cause > 60 % of those deaths
  4 survival  >= 80 % of today's level 05 on the same map
  5 hide      among fed states, cover share at injury >= 60 is >= 2x the share at injury <= 20
  6 comb      combination gain (tie margin 0.5) >= today's + max(5, 2 x noise floor, today's spread
              across tie margins 0 / 0.5 / 2); noise floor = |finer grid - today| on that map
A zero denominator makes a ratio "not computable" and fails its criterion. No threshold is tuned here.

  python balance_rule.py --sweep results/analysis/internal_state_interactions/balance
Writes <sweep>/balance_rule.json.
"""
import argparse, glob, json, os


def ratio(a, b):
    return None if not b else a / b


def criteria(r, base, noise, spread):
    ro = r["rollout"]; c = ro["counts"]; ts = ro["time_share"]; out = {}
    out["1_time"] = (max(ts.values()) <= 0.70) and all(ts[k] >= 0.10 for k in ("cover", "warm", "eat"))
    dr = ro["drive_ratio"]; wd = r["warming_per_decision"]["ratio"]
    out["2_drive"] = all(v is not None and v >= 2 for v in (dr.get("eat"), dr.get("hide"), wd))
    late = ro["deaths_after_early"]; n_late = sum(late.values())
    out["3_death"] = True if ro["late_death_share_of_starts"] < 0.05 else (max(late.values()) / n_late <= 0.60)
    out["4_survival"] = ro["survival_share"] >= 0.80 * base["rollout"]["survival_share"]
    hide = ratio(ratio(c["fed_cover_inj"], c["fed_n_inj"]) or 0.0, ratio(c["fed_cover_heal"], c["fed_n_heal"]))
    out["5_hide"] = hide is not None and hide >= 2
    g = r["summary_by_margin"]["0.5"]["combination_gain"]; gb = base["summary_by_margin"]["0.5"]["combination_gain"]
    need = max(0.05, 2 * noise, spread)
    out["6_comb"] = g - gb >= need
    detail = dict(time_share=ts, drive_ratio=dr, warming_per_decision=wd, late_deaths=late,
                  late_death_share=ro["late_death_share_of_starts"], survival=ro["survival_share"],
                  hide_ratio_fed=hide, comb_gain=g, comb_gain_minus_today=g - gb, comb_needed=need,
                  need_share=ro["need_share"])
    balanced = all(out[k] for k in ("1_time", "2_drive", "3_death", "4_survival", "5_hide"))
    verdict = ("balanced and combinational" if balanced and out["6_comb"] else "balanced, not combinational"
               if balanced else "combinational but one-sided" if out["6_comb"] else "neither")
    return out, detail, verdict


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sweep", required=True); a = ap.parse_args()
    R = {json.load(open(p))["name"]: json.load(open(p)) for p in glob.glob(os.path.join(a.sweep, "*__main.json"))}
    base = R["baseline__level-05__today"]; fin = R["check__finer-grid__81x41x91"]
    res = {}
    for m in ("warm0", "warm1"):
        b = base["per_map"][m]
        gm = [b["summary_by_margin"][k]["combination_gain"] for k in ("0.0", "0.5", "2.0")]
        noise = abs(fin["per_map"][m]["summary_by_margin"]["0.5"]["combination_gain"] - b["summary_by_margin"]["0.5"]["combination_gain"])
        spread = max(gm) - min(gm)
        res[f"_meta_{m}"] = dict(noise_floor=noise, margin_spread=spread, comb_needed=max(0.05, 2 * noise, spread))
        for name, r in R.items():
            if name.startswith("check__"):
                continue
            crit, det, verdict = criteria(r["per_map"][m], b, noise, spread)
            res.setdefault(name, {})[m] = dict(criteria=crit, verdict=verdict, **det)
    json.dump(res, open(os.path.join(a.sweep, "balance_rule.json"), "w"), indent=1)
    for name in sorted(k for k in res if not k.startswith("_")):
        v = res[name]["warm0"]; c = v["criteria"]
        print(f"{name:70s} {v['verdict']:28s} " + " ".join(f"{k[0]}{int(x)}" for k, x in c.items()))
    print({k: v for k, v in res.items() if k.startswith("_")})


if __name__ == "__main__":
    main()

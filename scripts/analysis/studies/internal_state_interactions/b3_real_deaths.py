"""TABLE B3 — What real (ordinary, no-modulator) agents die of in the level-05 pilot runs of 2026-09-27.

Reads each pilot's WandB summary (the final logging window of its 2,000,000 episodes; the pilots of
docs/experiments/active/level05_body_interactions/, manifest pilot_pick_manifest.yaml) and writes an
HTML table fragment: survival steps and the share of episodes ending in each way. Survival steps and
termination shares only; reward is never read.
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml
import _common as C

MAN = os.path.join(C.ROOT, "docs/experiments/active/level05_body_interactions/pilot_pick_manifest.yaml")
man = yaml.safe_load(open(MAN))
ROWS = [("P0a", "plain level 05, seed 42"), ("P0b", "plain level 05, seed 43"), ("P0c", "plain level 05, seed 44"),
        ("P01", "healing slower when hungry (half speed)"), ("P03", "healing slower when hungry (stops) — picked"),
        ("P04", "healing uses up food 0.5 — picked"), ("P06", "healing uses up food 2.0"),
        ("P07", "cold or hot uses up food, rate 2 — picked"), ("P09", "cold or hot uses up food, rate 8"),
        ("P10", "food per bite 4 — picked"), ("P11", "food per bite 3"), ("P14", "all four picked rules")]
runs = {}
for r in (man["runs"] if isinstance(man, dict) and "runs" in man else man):
    runs[str(r["id"])] = r
def wandb_summary(wid):
    d = glob.glob(os.path.join(C.ROOT, "wandb", f"run-*-{wid}", "files", "wandb-summary.json"))
    assert len(d) == 1, (wid, d)
    return json.load(open(d[0]))
out, used = [], 0
for pid, label in ROWS:
    if pid == "P14":
        wid = "438j1im3"
    else:
        r = runs[pid]; wid = r.get("wandb_id") or r.get("wandb")
    s = wandb_summary(wid); used += 1
    t = {k: s[f"Episode/Term_{k}"] for k in ("Injury", "Starvation", "Thermal", "Overeating", "MaxSteps")}
    died = t["Injury"] + t["Starvation"] + t["Thermal"] + t["Overeating"]
    out.append((label, s["Episode/Steps"], t, t["Injury"] / died if died else None))
cells = "".join(
    f'<tr><td>{l}</td><td class="n">{st:.0f}</td><td class="n">{100*t["MaxSteps"]:.0f}%</td>'
    f'<td class="n">{100*t["Injury"]:.0f}%</td><td class="n">{100*t["Starvation"]:.0f}%</td>'
    f'<td class="n">{100*(t["Thermal"]+t["Overeating"]):.0f}%</td><td class="n">{100*ij:.0f}%</td></tr>'
    for l, st, t, ij in out)
html = ('<p class="cue" hidden>Wider than the screen — scroll sideways.</p><div class="scroll"><table class="datatable wide">'
        '<thead><tr><th>pilot world</th><th class="n">survival steps</th><th class="n">reached 500</th>'
        '<th class="n">died of injury</th><th class="n">starved</th><th class="n">other</th>'
        '<th class="n">injury share of deaths</th></tr></thead><tbody>' + cells + '</tbody></table></div>')
os.makedirs(C.FIG, exist_ok=True)
open(os.path.join(C.FIG, "b3_real_deaths.html"), "w").write(html)
print(f"wrote b3_real_deaths.html ({used} runs)")

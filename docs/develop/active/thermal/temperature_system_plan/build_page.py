#!/usr/bin/env python
"""Builds index.html for the temperature-system plan. Figures are embedded as
base64 so the page is a single self-contained file. Regenerate with:

    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python build_page.py

Figures come from figs.py (field + body dynamics + rendering mock) and
nbhd_compare.py (thermoceptor neighbourhood accuracy). Numbers quoted in the
prose are recomputed here from sim.py so text and figures cannot drift apart.
"""
import base64, json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sim

def b64(p): return base64.b64encode(open(p, 'rb').read()).decode()
FIG = {k: b64(v) for k, v in {
    'pipeline': 'figA_pipeline.png', 'sigma': 'figB_sigma.png',
    'body': 'figC_body.png', 'render': 'figD_render.png',
    'nbhd': 'fig1_geometry.png', 'acc': 'fig3_accuracy.png'}.items()}

# --- recompute every number quoted in the prose ---
K_EX, K_LOSS, T_DEATH = 0.04, 0.01, 15.0
TAU = 1.0 / (K_EX + K_LOSS)
def equilib(tf): return K_EX * tf / (K_EX + K_LOSS)
def steps_to_death(tf):
    tr = sim.body_traj([tf] * 5000, k_ex=K_EX, k_loss=K_LOSS)
    i = int((abs(tr) >= T_DEATH).argmax())
    return i if i > 0 else None
K_CRIT = K_LOSS * T_DEATH / (20.0 - T_DEATH)
REC = int((sim.body_traj([0.0] * 400, T0=14.0, k_ex=K_EX, k_loss=K_LOSS) <= 5.0).argmax())
D20, D10 = steps_to_death(20.0), steps_to_death(10.0)
ACC = json.load(open('sweep2.json'))['res']

N = dict(tau=f'{TAU:.0f}', eq20=f'{equilib(20.0):+.0f}', eq10=f'{equilib(10.0):+.0f}',
         d20=str(D20), d10=('never' if D10 is None else str(D10)),
         kcrit=f'{K_CRIT:.3f}', rec=str(REC),
         vn1=f"{ACC['vN r=1']['err'][3]:.2f}", mo1=f"{ACC['Moore r=1']['err'][3]:.2f}",
         vn2=f"{ACC['vN r=2']['err'][3]:.2f}", mo2=f"{ACC['Moore r=2']['err'][3]:.2f}")

HTML = open('page_template.html').read()
for k, v in {**FIG, **N}.items():
    HTML = HTML.replace('@@' + k + '@@', v)
assert '@@' not in HTML, 'unreplaced token: ' + HTML[HTML.index('@@'):HTML.index('@@')+40]
open('index.html', 'w').write(HTML)
print(f'index.html written ({os.path.getsize("index.html")/1024:.0f} KB)')
print(f'  tau={N["tau"]}  eq(+20)={N["eq20"]}  death@+20={N["d20"]}  k_crit={N["kcrit"]}  recovery={N["rec"]}')

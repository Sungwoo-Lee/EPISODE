#!/usr/bin/env python
"""Builds index.html for the temperature-system plan.

Figures are embedded as base64 so the page is one self-contained file. Every
number quoted in the prose is recomputed here from sim.py, so the text cannot
drift away from the figures. Regenerate with:

    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python build_page.py
"""
import base64, json, os
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from sim import gaussian_smooth, body_traj, H, W

def b64(p): return base64.b64encode(open(p, 'rb').read()).decode()
FIG = {k: b64(v) for k, v in {
    'pipeline': 'figA_pipeline.png', 'sigma': 'figB_sigma.png', 'body': 'figC_body.png',
    'render': 'figD_render.png', 'tether': 'figE_tether.png',
    'nbhd': 'fig1_geometry.png', 'acc': 'fig3_accuracy.png'}.items()}

DEFAULT, SIGMA, K_EX, K_LOSS, DEATH = -25.0, 1.2, 0.04, 0.01, 15.0

def radial(A):
    raw = np.full((H, W), DEFAULT); raw[5, 5] += A
    f = gaussian_smooth(raw, SIGMA); out = {}
    for d in range(0, 11):
        c = [f[r, cc] for r in range(H) for cc in range(W) if abs(r-5)+abs(cc-5) == d]
        if not c: continue
        amb = float(np.mean(c))
        tr = body_traj([amb]*4000, k_ex=K_EX, k_loss=K_LOSS)
        i = int((np.abs(tr) >= DEATH).argmax())
        out[d] = (amb, K_EX*amb/(K_EX+K_LOSS), None if i == 0 else i)
    return out

R300, R900 = radial(300.0), radial(900.0)
safe300 = max(d for d in R300 if R300[d][2] is None)
safe900 = [d for d in R900 if R900[d][2] is None]
ACC = json.load(open('sweep2.json'))['res']

N = dict(
    tau=f'{1/(K_EX+K_LOSS):.0f}',
    default=f'{DEFAULT:.0f}', sigma=f'{SIGMA}',
    fire_eq=f'{R300[0][1]:+.1f}', d1=f'{R300[1][1]:+.1f}', d2=f'{R300[2][1]:+.1f}',
    d3=f'{R300[3][1]:+.1f}', d3_steps=str(R300[3][2]),
    far_eq=f'{R300[10][1]:+.1f}', far_steps=str(R300[10][2]),
    safe=str(safe300),
    kcrit=f'{K_LOSS*DEATH/(abs(DEFAULT)-DEATH):.3f}',
    h_d0=str(R900[0][2]), h_d1=str(R900[1][2]),
    h_d2=f'{R900[2][1]:+.1f}', h_d3=f'{R900[3][1]:+.1f}', h_d4=str(R900[4][2]),
    h_ring=f'{min(safe900)}–{max(safe900)}',
    vn1=f"{ACC['vN r=1']['err'][3]:.2f}", mo1=f"{ACC['Moore r=1']['err'][3]:.2f}",
    vn2=f"{ACC['vN r=2']['err'][3]:.2f}", mo2=f"{ACC['Moore r=2']['err'][3]:.2f}")

HTML = open('page_template.html').read()
for k, v in {**FIG, **N}.items():
    HTML = HTML.replace('@@' + k + '@@', v)
assert '@@' not in HTML, 'unreplaced token: ' + HTML[HTML.index('@@'):HTML.index('@@')+40]
open('index.html', 'w').write(HTML)
print(f'index.html written ({os.path.getsize("index.html")/1024:.0f} KB)')
for k, v in N.items(): print(f'  {k:10s} {v}')

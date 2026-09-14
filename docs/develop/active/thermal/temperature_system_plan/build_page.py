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
    'pipeline': 'figA_pipeline.png', 'fig_sigma': 'figB_sigma.png', 'body': 'figC_body.png',
    'render': 'figD_render.png', 'tether': 'figE_tether.png', 'modes': 'figF_modes.png', 'fig_kloss': 'figG_kloss.png', 'ranges': 'figH_ranges.png', 'pain': 'figI_pain.png',
    'nbhd': 'fig1_geometry.png', 'acc': 'fig3_accuracy.png',
    'obs': 'figJ_obs.png'}.items()}

DEFAULT, SIGMA, K_EX, K_LOSS, DEATH = -25.0, 0.7, 0.04, 0.01, 15.0
A_FIRE = 300.0

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

def rand_field(rng, default, n, temp, size, sigma):
    raw = np.full((H, W), float(default)); s = int(size)//2
    for _ in range(n):
        r, c = rng.integers(0, H), rng.integers(0, W); sign = rng.choice([-1, 1])
        for dr in range(-s, s+1):
            for dc in range(-s, s+1):
                rr, cc = r+dr, c+dc
                if 0 <= rr < H and 0 <= cc < W: raw[rr, cc] += sign*temp
    return gaussian_smooth(raw, sigma)

def pct_safe(temp, trials=200):
    rng = np.random.default_rng(3)
    v = [(np.abs(K_EX*rand_field(rng, 0, 4, temp, 2, SIGMA)/(K_EX+K_LOSS)) < DEATH).mean()
         for _ in range(trials)]
    return float(np.mean(v))*100

RAND = {t: pct_safe(t) for t in (20, 40, 120)}
_cf = np.full((H, W), DEFAULT); _cf[5, 5] += 300.0
CF_SAFE = float((np.abs(K_EX*gaussian_smooth(_cf, SIGMA)/(K_EX+K_LOSS)) < DEATH).mean())*100

def sample_world(rng, cnt, temp, dflt, margin=2):
    n = rng.integers(cnt[0], cnt[1]+1); d = rng.uniform(dflt[0], dflt[1])
    raw = np.full((H, W), d)
    for _ in range(n):
        r = rng.integers(margin, H-margin); c = rng.integers(margin, W-margin)
        raw[r, c] += rng.uniform(temp[0], temp[1])
    return gaussian_smooth(raw, SIGMA)

COMBOS = [('A', 'gentle',   (1, 2), (250, 300), (-25, -22)),
          ('B', 'moderate', (1, 3), (250, 350), (-28, -22)),
          ('C', 'harsh',    (1, 1), (250, 320), (-32, -28)),
          ('D', 'varied',   (1, 4), (200, 450), (-32, -20))]
CHAR = {'A': 'few, mild fires; the safest of the four',
        'B': 'the structure holds everywhere in the box - <strong>proposed</strong>',
        'C': 'one fire in a hard world; least forgiving',
        'D': 'widest; some draws lose the pain or the comfort ring'}

def structure_ok(A, dflt):
    """Does this draw give pain on the fire, safety beside it, and lethal cold beyond?"""
    raw = np.full((H, W), float(dflt)); raw[5, 5] += A
    f = gaussian_smooth(raw, SIGMA); o = {}
    for d in (0, 1, 3):
        c = [f[r, cc] for r in range(H) for cc in range(W) if abs(r-5)+abs(cc-5) == d]
        amb = float(np.mean(c))
        tr = body_traj([amb]*4000, k_ex=K_EX, k_loss=K_LOSS)
        i = int((np.abs(tr) >= DEATH).argmax())
        o[d] = (K_EX*amb/(K_EX+K_LOSS), None if i == 0 else i)
    return (o[0][0] > DEATH and o[0][1] is not None) and (o[1][1] is None) and (o[3][1] is not None)
rows = []
for tag, name, cnt, temp, dflt in COMBOS:
    r = np.random.default_rng(5)
    v = np.array([(np.abs(K_EX*sample_world(r, cnt, temp, dflt)/(K_EX+K_LOSS)) < DEATH).mean()*100
                  for _ in range(600)])
    p10, med, p90 = np.percentile(v, [10, 50, 90])
    r2 = np.random.default_rng(7)
    ok = np.mean([structure_ok(r2.uniform(*temp), r2.uniform(*dflt)) for _ in range(600)])*100
    cls = ' class="pick"' if tag == 'B' else ''
    rows.append(f'<tr{cls}><td><strong>{tag}</strong> {name}</td>'
                f'<td class="n">{cnt[0]}&ndash;{cnt[1]}</td>'
                f'<td class="n">{temp[0]}&ndash;{temp[1]}</td>'
                f'<td class="n">{dflt[0]} to {dflt[1]}</td>'
                f'<td class="n">{p10:.0f}&ndash;{p90:.0f}%</td>'
                f'<td class="n">{med:.0f}%</td>'
                f'<td class="n">{ok:.0f}%</td><td>{CHAR[tag]}</td></tr>')
COMBO_ROWS = '\n'.join(rows)

R300, R900 = radial(300.0), radial(900.0)
R_PAIN = radial(A_FIRE)

def _burn(A=A_FIRE, dflt=DEFAULT):
    raw = np.full((H, W), float(dflt)); raw[5, 5] += A
    f = gaussian_smooth(raw, SIGMA)
    amb = {d: float(np.mean([f[r, c] for r in range(H) for c in range(W)
                             if abs(r-5)+abs(c-5) == d])) for d in (0, 1)}
    T = K_EX*amb[1]/(K_EX+K_LOSS)
    for k in range(30):
        T = T + K_EX*(amb[0]-T) - K_LOSS*T
        if abs(T) >= DEATH: return k+1, amb[0]
    return None, amb[0]

BURN, PEAK = _burn()
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
    combo_rows=COMBO_ROWS,
    pain_eq=f'{R_PAIN[0][1]:.0f}', pain_steps=str(R_PAIN[0][2]),
    burn=str(BURN), peak=f'{PEAK:.0f}',
    comfy_eq=f'{R_PAIN[1][1]:.1f}', cool_eq=f'{R_PAIN[2][1]:.1f}',
    cold_steps=str(R_PAIN[3][2]), afire=f'{A_FIRE:.0f}',
    adopted=f'{K_EX/(K_EX+K_LOSS)*100:.0f}',
    held=f'{K_LOSS/(K_EX+K_LOSS)*100:.0f}',
    window=f'{DEATH*(K_EX+K_LOSS)/K_EX:.1f}',
    kceil=f'{K_EX*(abs(DEFAULT)/DEATH-1):.3f}',
    kloss=f'{K_LOSS}', kex=f'{K_EX}',
    r20=f'{RAND[20]:.0f}', r40=f'{RAND[40]:.0f}', r120=f'{RAND[120]:.0f}',
    cf_safe=f'{CF_SAFE:.0f}',
    vn1=f"{ACC['vN r=1']['err'][3]:.2f}", mo1=f"{ACC['Moore r=1']['err'][3]:.2f}",
    vn2=f"{ACC['vN r=2']['err'][3]:.2f}", mo2=f"{ACC['Moore r=2']['err'][3]:.2f}")

# ---- the worked walk quoted in section 13 (same recurrence as figJ_obs.py) ----
_raw = np.full((H, W), DEFAULT); _raw[5, 5] += A_FIRE
_FLD = gaussian_smooth(_raw, SIGMA)
_PATH = [(5, 0), (5, 1), (5, 2), (5, 3)] + [(5, 4)] * 46
_T = 0.0; _walk = []
for (_r, _c) in _PATH:
    _f = float(_FLD[_r, _c])
    _walk.append((_T, _f - _T, _f))
    _T = _T + K_EX * (_f - _T) - K_LOSS * (_T - 0.0)
def _w(i, j): return f'{_walk[i][j]:+.2f}'
N.update(
    ob_dim_before='32', ob_dim_after='33',
    ob_body0=_w(0, 0),  ob_th0=_w(0, 1),  ob_cell0=_w(0, 2),
    ob_body12=_w(12, 0), ob_th12=_w(12, 1), ob_cell12=_w(12, 2),
    ob_body40=_w(40, 0), ob_th40=_w(40, 1), ob_cell40=_w(40, 2),
    ob_sum12=f'{_walk[12][0] + _walk[12][1]:+.2f}',
    ob_sum40=f'{_walk[40][0] + _walk[40][1]:+.2f}',
    ob_thdiff=f'{abs(_walk[12][1] - _walk[40][1]):.2f}',
)

clash = set(FIG) & set(N)
assert not clash, f'token name collision between figures and numbers: {clash}'

HTML = open('page_template.html').read()
for k, v in {**FIG, **N}.items():
    HTML = HTML.replace('@@' + k + '@@', v)
assert '@@' not in HTML, 'unreplaced token: ' + HTML[HTML.index('@@'):HTML.index('@@')+40]
open('index.html', 'w').write(HTML)
print(f'index.html written ({os.path.getsize("index.html")/1024:.0f} KB)')
for k, v in N.items(): print(f'  {k:10s} {v}')

"""Figures for the temperature-system plan. Cold world + campfire, EVAAA's design."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Rectangle, Circle
import numpy as np
from sim import gaussian_smooth, body_traj, H, W

SURF='#fcfcfb'; INK='#16181d'; INK2='#4e545e'; GRID='#e3e2de'
C1='#2a78d6'; C2='#eb6834'; C3='#1baf7a'; C4='#4a3aa7'
DIV=LinearSegmentedColormap.from_list('bt',['#184f95','#6da7ec','#f0efec','#e08a8a','#b02b2b'])
plt.rcParams.update({'figure.dpi':100,'figure.facecolor':SURF,'axes.facecolor':SURF,
 'savefig.facecolor':SURF,'text.color':INK,'axes.labelcolor':INK2,'xtick.color':INK2,
 'ytick.color':INK2,'axes.edgecolor':GRID,'font.size':10,'axes.titlesize':11,
 'axes.titleweight':'bold'})
def bare(ax):
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)

DEFAULT, A_FIRE, SIGMA = -25.0, 300.0, 0.7
K_EX, K_LOSS, DEATH = 0.04, 0.01, 15.0
FIRES=[(5,5)]; BUSH=[(2,7),(3,7)]

def build(default=DEFAULT, fires=FIRES, A=A_FIRE, bush_t=0.0, sigma=SIGMA):
    raw=np.full((H,W),float(default)); st={'fill':raw.copy()}
    for (r,c) in fires: raw[r,c]+=A
    st['fire']=raw.copy()
    for (r,c) in BUSH: raw[r,c]+=bush_t
    st['objects']=raw.copy()
    st['smoothed']=gaussian_smooth(raw,sigma)
    return st

def radial(f, fire=(5,5)):
    out={}
    for d in range(0,11):
        c=[f[r,cc] for r in range(H) for cc in range(W) if abs(r-fire[0])+abs(cc-fire[1])==d]
        if not c: continue
        amb=float(np.mean(c)); tr=body_traj([amb]*4000,k_ex=K_EX,k_loss=K_LOSS)
        i=int((np.abs(tr)>=DEATH).argmax())
        out[d]=(amb, K_EX*amb/(K_EX+K_LOSS), None if i==0 else i)
    return out

st=build(bush_t=-6.0)
M=max(abs(st['smoothed']).max(), 25.0); NRM=TwoSlopeNorm(0,-M,M)

# ---------- FIG A : construction ----------
fig,axes=plt.subplots(1,4,figsize=(13.2,3.8))
for ax,(k,t) in zip(axes,[('fill','1. fill  default_temp = -25'),('fire','2. + campfire  (+300)'),
                          ('objects','3. + other object temps'),('smoothed','4. Gaussian smooth  sigma = 1.2')]):
    ax.imshow(st[k],cmap=DIV,norm=NRM); ax.set_title(t,color=INK,fontsize=10.5); bare(ax)
    if k!='fill':
        for (r,c) in FIRES: ax.add_patch(Circle((c,r),.42,fc='none',ec=INK,lw=1.6))
    if k in ('objects','smoothed'):
        for (r,c) in BUSH: ax.add_patch(Rectangle((c-.5,r-.5),1,1,fc='none',ec=INK,lw=1.2,ls=':'))
fig.suptitle('Building the field — a cold world with the campfire as its only warmth',
             fontsize=12.5,fontweight='bold')
fig.text(.5,.02,'Circled cell is the campfire; dotted cells are a shaded bush pair at -6. Every object '
 'type carries a temperature, almost all of them zero. Stamps ADD, then one blur at the end.',
 ha='center',color=INK2,fontsize=9)
fig.tight_layout(rect=[0,.07,1,.90]); fig.savefig('figA_pipeline.png',dpi=140,bbox_inches='tight'); plt.close(fig)

# ---------- FIG B : sigma ----------
sigmas=[0.0,0.5,0.8,1.2,2.0,4.0]
raw=build(bush_t=-6.0)['objects']; MB=40.0; nb=TwoSlopeNorm(0,-MB,MB)
fig=plt.figure(figsize=(12.6,6.4)); gs=fig.add_gridspec(2,6,height_ratios=[1.15,1],hspace=.48,wspace=.18)
for i,sg in enumerate(sigmas):
    ax=fig.add_subplot(gs[0,i]); f=gaussian_smooth(raw,sg)
    im=ax.imshow(f,cmap=DIV,norm=nb); ax.set_title(f'sigma = {sg}',color=INK,fontsize=10.5)
    r=radial(f); safe=[d for d in r if r[d][2] is None]
    ax.set_xlabel(f'safe radius {max(safe) if safe else 0}',fontsize=8.5,color=INK2,labelpad=3); bare(ax)
cb=fig.colorbar(im,ax=[fig.axes[i] for i in range(6)],fraction=.016,pad=.012)
cb.set_label('cell temperature',fontsize=8.5,color=INK2); cb.ax.tick_params(labelsize=8,colors=INK2)
cb.outline.set_visible(False)
ss=np.linspace(0.05,4,45); peak=[]; sr=[]
for sg in ss:
    f=gaussian_smooth(raw,sg); peak.append(f.max()); r=radial(f)
    s=[d for d in r if r[d][2] is None]; sr.append(max(s) if s else 0)
axL=fig.add_subplot(gs[1,0:3]); axR=fig.add_subplot(gs[1,3:6])
axL.plot(ss,peak,color=C1,lw=2.2); axL.set_ylabel('peak temperature at the fire',fontsize=9.5)
axR.step(ss,sr,color=C1,lw=2.2,where='mid'); axR.set_ylabel('safe radius (cells)',fontsize=9.5)
for ax,t in ((axL,'The fire concentrates as sigma falls'),(axR,'How much of the map is survivable')):
    ax.set_xlabel('smoothing sigma'); ax.set_title(t,color=INK,fontsize=10.5)
    ax.axvspan(1.0,1.5,color=C3,alpha=.14); ax.grid(True,color=GRID,lw=.8); ax.set_axisbelow(True)
    ax.set_xlim(0,4)
    for s_ in ('top','right'): ax.spines[s_].set_visible(False)
axR.set_yticks([0,1,2,3,4])
axL.annotate('proposed 1.2',(1.25,max(peak)*.6),ha='center',fontsize=9,color='#0f7a55',fontweight='bold')
fig.suptitle('Smoothing sigma decides how far the fire reaches',fontsize=13,fontweight='bold',y=.98)
fig.text(.5,.005,'One shared colour scale across all six panels. Too sharp and the warmth never leaves the '
 'fire cell; too smooth and it spreads until the whole map is uniformly survivable and the fire stops '
 'mattering.',ha='center',color=INK2,fontsize=9)
fig.savefig('figB_sigma.png',dpi=140,bbox_inches='tight'); plt.close(fig)

# ---------- FIG E : the tether ----------
fig,axes=plt.subplots(1,3,figsize=(13.5,4.4))
prof={A:radial(gaussian_smooth(np.where(np.arange(H*W).reshape(H,W)>=0,DEFAULT,DEFAULT)
        + np.pad([[A]],((5,4),(5,4))), SIGMA)) for A in (300.0,900.0)}
ax=axes[0]
for A,col,lab in [(300.0,C1,'A = 300  (hearth)'),(900.0,C2,'A = 900  (approach-avoidance)')]:
    ds=sorted(prof[A]); ax.plot(ds,[prof[A][d][1] for d in ds],color=col,lw=2.2,marker='o',ms=5,label=lab)
ax.axhspan(-DEATH,DEATH,color=C3,alpha=.12)
ax.axhline(DEATH,color=INK,ls=':',lw=1.2); ax.axhline(-DEATH,color=INK,ls=':',lw=1.2)
ax.text(5.0,DEATH+4,'heat death',ha='center',fontsize=8.5,color=INK)
ax.text(7.5,-DEATH-9,'cold death',ha='center',fontsize=8.5,color=INK)
ax.text(0.3,DEATH-6,'survivable band',fontsize=8.5,color='#0f7a55',fontweight='bold')
ax.set_xlabel('Manhattan distance from the fire'); ax.set_ylabel('equilibrium body temperature')
ax.set_title('Where the agent can settle',color=INK)
ax.legend(frameon=False,fontsize=8.5,loc='upper right',bbox_to_anchor=(1.0,.97))
ax.set_ylim(-32,68)
ax=axes[1]
for _i,(A,col) in enumerate([(300.0,C1),(900.0,C2)]):
    ds=sorted(prof[A]); y=[prof[A][d][2] if prof[A][d][2] else np.nan for d in ds]
    ax.plot(ds,y,color=col,lw=2.2,marker='o',ms=5)
    safe=[d for d in ds if prof[A][d][2] is None]
    if safe: ax.axvspan(min(safe)-.45,max(safe)+.45,color=col,alpha=.13)
    if safe: ax.annotate(f'safe d={min(safe)}-{max(safe)}',(np.mean(safe),46-_i*6),ha='center',
                         fontsize=8.5,color=col,fontweight='bold')
ax.set_xlabel('Manhattan distance from the fire'); ax.set_ylabel('steps until death')
ax.set_title('How long you may linger',color=INK)
ax.set_ylim(0,56); ax.text(9.8,7,'shaded = survivable\nindefinitely',ha='right',fontsize=8.5,color=INK2)
ax=axes[2]
f=gaussian_smooth(np.full((H,W),DEFAULT)+np.pad([[A_FIRE]],((5,4),(5,4))),SIGMA)
ax.imshow(f,cmap=DIV,norm=TwoSlopeNorm(0,-40,40))
r=radial(f); safe=max([d for d in r if r[d][2] is None])
for rr in range(H):
    for cc in range(W):
        if abs(rr-5)+abs(cc-5)==safe:
            ax.add_patch(Rectangle((cc-.5,rr-.5),1,1,fc='none',ec=INK,lw=1.5))
ax.add_patch(Circle((5,5),.42,fc='none',ec=INK,lw=2))
ax.set_title(f'A = 300: safe out to d = {safe}',color=INK); bare(ax)
for a in axes[:2]:
    a.grid(True,color=GRID,lw=.8); a.set_axisbelow(True)
    for s_ in ('top','right'): a.spines[s_].set_visible(False)
fig.suptitle('The thermal tether — how far the agent may roam before it must return',
             fontsize=12.5,fontweight='bold')
fig.text(.5,.02,'A weak fire (A=300) makes a warm hearth you sit on. A strong one (A=900) is lethal at the '
 'centre and comfortable in a ring around it, so the agent must find the annulus rather than the point.',
 ha='center',color=INK2,fontsize=9)
fig.tight_layout(rect=[0,.07,1,.91]); fig.savefig('figE_tether.png',dpi=140,bbox_inches='tight'); plt.close(fig)

# ---------- FIG C : body dynamics ----------
fig,axes=plt.subplots(1,3,figsize=(13.2,4.1))
ax=axes[0]
# Ambients are read off the real radial profile, never typed. An earlier version of
# this panel hard-coded them and labelled a +8 cell "at the fire"; the fire cell is
# actually +72 and lethal, which contradicted section 04's own prose.
_RP=radial(st['smoothed'])
_AMB={d:_RP[d][0] for d in _RP}
# d=3 and the far field settle within 0.4 deg of each other, so the two curves
# overlap; the far field is dashed to keep five legend entries honest.
for d,col,lab,ls in [(0,'#b02b2b','d=0, on the fire','-'),(1,'#eb6834','d=1, the comfort ring','-'),
                     (2,'#e08a8a','d=2','-'),(3,'#6da7ec','d=3','-'),
                     (4,'#184f95','far field','--')]:
    tr=body_traj([_AMB[d]]*500,k_ex=K_EX,k_loss=K_LOSS)
    hit=np.nonzero(np.abs(tr)>=DEATH)[0]
    lab=f'{lab}  ({_AMB[d]:+.0f})'
    if len(hit) and tr[hit[0]]>0:                 # heat death: clip, do not rescale
        k=hit[0]; ax.plot(tr[:k+1],color=col,lw=2,ls=ls,label=lab)
        ax.plot([k],[DEATH],marker='x',ms=8,mew=2.2,color=col)
        ax.annotate(f'off the top at step {k} —\nsettles near {K_EX*_AMB[d]/(K_EX+K_LOSS):+.0f}',
                    (k+12,DEATH-1.0),fontsize=8.2,color=col,va='top')
    else:
        ax.plot(tr,color=col,lw=2,ls=ls,label=lab)
ax.axhline(-DEATH,color=INK,ls=':',lw=1.3); ax.axhline(DEATH,color=INK,ls=':',lw=1.3)
ax.text(250,-DEATH-1.2,'cold death',ha='center',va='top',fontsize=8.5,color=INK)
ax.text(250,DEATH+1.0,'heat death',ha='center',va='bottom',fontsize=8.5,color=INK)
ax.set_xlabel('step'); ax.set_ylabel('body temperature'); ax.set_xlim(0,500); ax.set_ylim(-25,21)
ax.set_title('Body temp at each distance',color=INK)
ax.legend(frameon=False,fontsize=7.6,loc='center right',bbox_to_anchor=(1.0,0.42))
ax=axes[1]
# Same profile: out at d=3, back to the comfort ring at d=1.
_OUT,_RING=_AMB[3],_AMB[1]
seq=[_RING]*45+([_OUT]*30+[_RING]*40)*2+[_OUT]*45
tr=body_traj(seq,k_ex=K_EX,k_loss=K_LOSS); _d=int((np.abs(tr)>=DEATH).argmax())
ax.plot(tr,color=C1,lw=2.2)
for a,b in [(45,75),(115,145),(185,len(tr)-1)]: ax.axvspan(a,b,color=C1,alpha=.09)
ax.axhline(-DEATH,color=INK,ls=':',lw=1.3)
ax.plot([_d],[tr[_d]],marker='x',ms=9,mew=2.4,color='#b02b2b')
ax.annotate(f'two 30-step trips survive,\nbottoming at {tr[75]:+.1f} and {tr[145]:+.1f}',
            (60,-23.2),fontsize=8.3,color=INK2)
ax.annotate(f'a 45-step trip does not —\ndead {_d-185} steps out',(190,4.5),fontsize=8.3,color='#b02b2b')
ax.set_xlabel('step'); ax.set_title('A foraging cycle  (shaded = away from fire)',color=INK)
ax.set_xlim(0,len(tr)-1); ax.set_ylim(-25,21)
ax=axes[2]
ks=np.linspace(0.005,0.12,120); tt=[]
for kx in ks:
    tr=body_traj([-25.0]*6000,k_ex=kx,k_loss=K_LOSS); i=int((np.abs(tr)>=DEATH).argmax())
    tt.append(i if i>0 else np.nan)
tt=np.array(tt,float); kc=K_LOSS*DEATH/(25.0-DEATH)
ax.axvspan(ks[0],kc,color='#8a8f97',alpha=.16)
ax.plot(ks,tt,color=C1,lw=2.2); ax.axvline(K_EX,color=C3,lw=1.8)
i0=int(np.nanargmin(np.abs(ks-K_EX))); ax.plot([K_EX],[tt[i0]],marker='o',ms=7,color=C3,zorder=5)
ax.annotate(f'proposed 0.04\n{int(tt[i0])} steps',(K_EX,tt[i0]),textcoords='offset points',
            xytext=(14,24),fontsize=9,color='#0f7a55',fontweight='bold')
ax.text((ks[0]+kc)/2,np.nanmax(tt)*.5,'cold never\nkills',ha='center',fontsize=8.8,color='#5c6068',fontweight='bold')
ax.set_xlabel('k_exchange'); ax.set_ylabel('steps to cold death in the far field')
ax.set_xlim(ks[0],ks[-1]); ax.set_ylim(0,np.nanmax(tt)*1.25)
ax.set_title('Choosing k_exchange   (k_loss = 0.01)',color=INK)
for a in axes:
    a.grid(True,color=GRID,lw=.8); a.set_axisbelow(True)
    for s_ in ('top','right'): a.spines[s_].set_visible(False)
fig.suptitle('Body temperature is a first-order lag toward the cell you are standing on',
             fontsize=12.5,fontweight='bold')
fig.tight_layout(rect=[0,.02,1,.92]); fig.savefig('figC_body.png',dpi=140,bbox_inches='tight'); plt.close(fig)

# ---------- FIG D : rendering ----------
fig,axes=plt.subplots(1,2,figsize=(11,5.0))
ents={'food':[(1,2),(8,6)],'pred':[(4,8)],'bush':BUSH,'rock':[(7,2),(6,3)]}
COLS={'food':'#0ca30c','pred':'#d03b3b','bush':'#1baf7a','rock':'#7a7168'}
agent=(5,3)
fld=build(bush_t=-6.0)['smoothed']
for ax,show in zip(axes,[False,True]):
    if show: ax.imshow(fld,cmap=DIV,norm=TwoSlopeNorm(0,-40,40),alpha=.9)
    else: ax.imshow(np.zeros((H,W)),cmap='Greys',vmin=0,vmax=1)
    for i in range(H+1):
        ax.axhline(i-.5,color=GRID,lw=.6); ax.axvline(i-.5,color=GRID,lw=.6)
    for k,ps in ents.items():
        for (r,c) in ps: ax.add_patch(Circle((c,r),.30,fc=COLS[k],ec=SURF,lw=1.4,zorder=3))
    for (r,c) in FIRES:
        ax.add_patch(Circle((c,r),.34,fc='#ff8c1a',ec=SURF,lw=1.6,zorder=3))
        ax.plot([c],[r],marker='*',ms=9,color='#fff3d6',zorder=4)
    ax.add_patch(Circle((agent[1],agent[0]),.34,fc=INK,ec=SURF,lw=1.6,zorder=5))
    if show:
        for dr,dc in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]:
            ax.add_patch(Rectangle((agent[1]+dc-.5,agent[0]+dr-.5),1,1,fc='none',ec='#111',lw=1.7,zorder=6))
    ax.set_xlim(-.5,W-.5); ax.set_ylim(H-.5,-.5); bare(ax)
    ax.set_title('current render' if not show else 'proposed: field underlay + read cells',
                 color=INK,fontsize=11)
fig.suptitle('Rendering — temperature underneath, entities unchanged on top',fontsize=12.5,fontweight='bold')
fig.text(.5,.03,'Orange star is the campfire. Black outline marks the five cells the thermoceptor reads. '
 'Colour limits are fixed for the whole episode so a cooling world does not look stable.',
 ha='center',color=INK2,fontsize=9)
fig.tight_layout(rect=[0,.08,1,.92]); fig.savefig('figD_render.png',dpi=140,bbox_inches='tight'); plt.close(fig)
print('figures rebuilt: A B C D E')

# ---------- FIG F : the two field modes ----------
def rand_field(rng, default, n, temp, size, sigma):
    raw=np.full((H,W),float(default)); s=int(size)//2
    for _ in range(n):
        r,c=rng.integers(0,H),rng.integers(0,W); sign=rng.choice([-1,1])
        for dr in range(-s,s+1):
            for dc in range(-s,s+1):
                rr,cc=r+dr,c+dc
                if 0<=rr<H and 0<=cc<W: raw[rr,cc]+=sign*temp
    return gaussian_smooth(raw,sigma)
def eqf(f): return K_EX*f/(K_EX+K_LOSS)

fig=plt.figure(figsize=(13.0,6.4))
gs=fig.add_gridspec(2,4,height_ratios=[1,.95],hspace=.42,wspace=.20)
rng=np.random.default_rng(3); NR=TwoSlopeNorm(0,-45,45)
def mark(ax,f):
    e=eqf(f)
    for r in range(H):
        for c in range(W):
            if abs(e[r,c])>=DEATH:
                ax.add_patch(Rectangle((c-.5,r-.5),1,1,fc='none',ec=INK,lw=1.1,ls=':'))
    return (np.abs(e)<DEATH).mean()*100
for i in range(3):
    ax=fig.add_subplot(gs[0,i]); f=rand_field(rng,0,4,40,2,1.2)
    ax.imshow(f,cmap=DIV,norm=NR); pct=mark(ax,f)
    ax.set_title(f'random  #{i+1}',color=INK,fontsize=10.5)
    ax.set_xlabel(f'{pct:.0f}% safe',fontsize=9.5,color=INK2,labelpad=3); bare(ax)
ax=fig.add_subplot(gs[0,3])
raw=np.full((H,W),-25.0); raw[5,5]+=300.0; f=gaussian_smooth(raw,1.2)
ax.imshow(f,cmap=DIV,norm=NR); pct=mark(ax,f)
ax.add_patch(Circle((5,5),.42,fc='none',ec=INK,lw=2))
ax.set_title('campfire',color=INK,fontsize=10.5)
ax.set_xlabel(f'{pct:.0f}% safe',fontsize=9.5,color=INK2,labelpad=3); bare(ax)

axL=fig.add_subplot(gs[1,0:4])
temps=[20,30,40,60,80,120]; sf=[]
for t in temps:
    r2=np.random.default_rng(3); v=[(np.abs(eqf(rand_field(r2,0,4,t,2,1.2)))<DEATH).mean()
                                   for _ in range(200)]
    sf.append(np.mean(v)*100)
axL.axhspan(50,85,color=C3,alpha=.12)
axL.plot(temps,sf,color=C1,lw=2.4,marker='o',ms=7,label='random mode')
axL.axhline(13.0,color=C2,lw=2.2,ls='--',label='campfire mode (13% safe)')
axL.annotate('useful difficulty band',(26,68),fontsize=9.5,color='#0f7a55',fontweight='bold')
axL.annotate('proposed 40',(40,sf[2]),textcoords='offset points',xytext=(10,16),
             fontsize=9.5,color=C1,fontweight='bold')
axL.set_xlabel('random spot temperature'); axL.set_ylabel('% of the map survivable')
axL.set_title('The two modes sit at opposite ends of the same axis',color=INK)
axL.set_ylim(0,100); axL.legend(frameon=False,fontsize=9,loc='upper right')
axL.grid(True,color=GRID,lw=.8); axL.set_axisbelow(True)
for s_ in ('top','right'): axL.spines[s_].set_visible(False)
fig.suptitle('Two ways to build the field — chosen by configuration, not baked in',
             fontsize=13,fontweight='bold',y=.98)
fig.text(.5,.005,'Dotted cells are lethal at equilibrium. Random spots scatter hazards through an '
 'otherwise safe world; a campfire puts one refuge in an otherwise lethal one. Both flags exist in '
 'EVAAA and both can be on at once.',ha='center',color=INK2,fontsize=9)
fig.savefig('figF_modes.png',dpi=140,bbox_inches='tight'); plt.close(fig)
print('figF written')

# ---------- FIG G : what k_loss does ----------
fig=plt.figure(figsize=(13.2,4.6))
gs=fig.add_gridspec(1,3,wspace=.30)

# panel 1 — the tug of war
ax=fig.add_subplot(gs[0,0])
TF, SP = -25.0, 0.0
Tstar = K_EX*TF/(K_EX+K_LOSS)
ax.set_xlim(-32,11); ax.set_ylim(-1.5,2.05)
ax.axhline(0,color=GRID,lw=1.8)
ax.plot([TF],[0],marker='o',ms=11,color='#184f95',zorder=4)
ax.annotate('T_field\nthe cell you stand on\n-25',(TF,0),textcoords='offset points',
            xytext=(0,-16),ha='center',va='top',fontsize=9,color='#184f95',fontweight='bold')
ax.plot([SP],[0],marker='s',ms=10,color='#5c6068',zorder=4)
ax.annotate('setpoint\n0',(SP,0),textcoords='offset points',xytext=(0,-16),ha='center',
            va='top',fontsize=9,color='#5c6068',fontweight='bold')
ax.plot([Tstar],[0],marker='D',ms=14,color=C2,zorder=5)
ax.annotate(f'body settles here  {Tstar:.0f}',(Tstar,0),textcoords='offset points',
            xytext=(0,11),ha='center',va='bottom',fontsize=9.5,color=C2,fontweight='bold')
ax.annotate('',xy=(TF+.8,1.30),xytext=(Tstar,1.30),
            arrowprops=dict(arrowstyle='-|>',lw=4,color='#184f95'))
ax.annotate(f'k_exchange = {K_EX}   pulls toward the world',(-12.5,1.52),ha='center',
            fontsize=9.2,color='#184f95',fontweight='bold')
ax.annotate('',xy=(SP-.8,0.62),xytext=(Tstar,0.62),
            arrowprops=dict(arrowstyle='-|>',lw=1.6,color='#5c6068'))
ax.annotate(f'k_loss = {K_LOSS}   pulls toward the setpoint',(-10,0.80),ha='center',
            fontsize=9.2,color='#5c6068',fontweight='bold')
ax.annotate('80% of the way to the cell, 20% held back',(-10.5,-1.32),ha='center',
            fontsize=9,color=INK2,style='italic')
ax.set_yticks([]); ax.set_xlabel('temperature')
for s_ in ('top','right','left'): ax.spines[s_].set_visible(False)
ax.set_title('A tug of war between two attractors',color=INK)

# panel 2 — trajectories
ax=fig.add_subplot(gs[0,1])
for kl,col in [(0.0,'#184f95'),(0.01,C1),(0.02,C3),(0.04,C2)]:
    tr=body_traj([-25.0]*400,k_ex=K_EX,k_loss=kl)
    i=int((np.abs(tr)>=DEATH).argmax())
    ax.plot(tr,color=col,lw=2.2,label=f'k_loss = {kl}' + ('  (never dies)' if i==0 else f'  (dies at {i})'))
ax.axhline(-DEATH,color=INK,ls=':',lw=1.4)
ax.text(200,-13.6,'death threshold',ha='center',fontsize=8.5,color=INK)
ax.set_xlabel('step'); ax.set_ylabel('body temperature')
ax.set_title('Standing in the far field  (-25)',color=INK)
ax.legend(frameon=False,fontsize=8.5,loc='lower left'); ax.set_ylim(-27,2); ax.set_xlim(0,400)

# panel 3 — survivable window
ax=fig.add_subplot(gs[0,2])
kls=np.linspace(0,0.05,200)
win=DEATH*(K_EX+kls)/K_EX
k_ceiling=K_EX*(25.0/DEATH-1)
ax.plot(kls,win,color=C1,lw=2.4)
ax.axhline(25,color=C2,lw=2,ls='--')
ax.annotate('our world is -25 cold',(0.049,25.9),ha='right',fontsize=9,color=C2,fontweight='bold')
ax.axvspan(k_ceiling,0.05,color='#8a8f97',alpha=.20)
ax.annotate('above here the world\ncan never kill you',( (k_ceiling+0.05)/2, 19),ha='center',
            fontsize=8.8,color='#4e545e',fontweight='bold')
ax.axvline(K_LOSS,color=C3,lw=1.8)
ax.plot([K_LOSS],[DEATH*(K_EX+K_LOSS)/K_EX],marker='o',ms=7,color=C3,zorder=5)
ax.annotate(f'proposed {K_LOSS}\nsurvives to +/-{DEATH*(K_EX+K_LOSS)/K_EX:.1f}',
            (K_LOSS,DEATH*(K_EX+K_LOSS)/K_EX),textcoords='offset points',xytext=(12,-30),
            fontsize=9,color='#0f7a55',fontweight='bold')
ax.set_xlabel('k_loss'); ax.set_ylabel('coldest ambient you can survive')
ax.set_title('k_loss decides how hostile the world may be',color=INK)
ax.set_xlim(0,0.05); ax.set_ylim(13,35)
for a in fig.axes[1:]:
    a.grid(True,color=GRID,lw=.8); a.set_axisbelow(True)
    for s_ in ('top','right'): a.spines[s_].set_visible(False)
fig.suptitle('k_loss is the strength of the body\'s own thermoregulation',
             fontsize=13,fontweight='bold',y=.99)
fig.text(.5,-.02,'With k_loss = 0 the body is a passive thermometer: it adopts the cell\'s temperature '
 'exactly and the setpoint means nothing. Raise it too far and the body defends so well that no cell '
 'in the world can hurt it, and the thermal task disappears.',ha='center',color=INK2,fontsize=9)
fig.savefig('figG_kloss.png',dpi=140,bbox_inches='tight'); plt.close(fig)
print('figG written')

# ---------- FIG H : ranges, not fixed values ----------
def sample_world(rng, cnt, temp, dflt, sigma=SIGMA, margin=2):
    n=rng.integers(cnt[0],cnt[1]+1); d=rng.uniform(dflt[0],dflt[1])
    raw=np.full((H,W),d); pos=[]
    for _ in range(n):
        r=rng.integers(margin,H-margin); c=rng.integers(margin,W-margin)
        raw[r,c]+=rng.uniform(temp[0],temp[1]); pos.append((r,c))
    return gaussian_smooth(raw,sigma), n, d, pos
def pct_safe(f):
    return (np.abs(K_EX*f/(K_EX+K_LOSS))<DEATH).mean()*100

COMBOS=[('A  gentle',   dict(cnt=(1,2),temp=(300,600),dflt=(-22,-18))),
        ('B  moderate', dict(cnt=(1,3),temp=(200,600),dflt=(-30,-22))),
        ('C  harsh',    dict(cnt=(1,1),temp=(150,350),dflt=(-35,-28))),
        ('D  varied',   dict(cnt=(1,4),temp=(150,700),dflt=(-35,-18)))]

fig=plt.figure(figsize=(13.2,6.6))
gs=fig.add_gridspec(2,6,height_ratios=[1,1.0],hspace=.42,wspace=.20)
rng=np.random.default_rng(5); NR=TwoSlopeNorm(0,-45,45)
for i in range(6):
    ax=fig.add_subplot(gs[0,i]); f,n,d,pos=sample_world(rng,**COMBOS[1][1])
    ax.imshow(f,cmap=DIV,norm=NR)
    for (r,c) in pos: ax.add_patch(Circle((c,r),.40,fc='none',ec=INK,lw=1.7))
    ax.set_title(f'{n} fire{"s" if n>1 else ""}',color=INK,fontsize=10)
    ax.set_xlabel(f'{pct_safe(f):.0f}% safe',fontsize=9,color=INK2,labelpad=3); bare(ax)

ax=fig.add_subplot(gs[1,0:6])
ys=np.arange(len(COMBOS))[::-1]
for (lab,cfg),y in zip(COMBOS,ys):
    r2=np.random.default_rng(5)
    v=np.array([pct_safe(sample_world(r2,**cfg)[0]) for _ in range(600)])
    p10,med,p90=np.percentile(v,[10,50,90])
    ax.plot([p10,p90],[y,y],color=C1,lw=7,solid_capstyle='round',alpha=.32)
    ax.plot([med],[y],marker='o',ms=11,color=C1,zorder=4)
    ax.annotate(f'{p10:.0f}–{p90:.0f}%',(p90,y),textcoords='offset points',xytext=(14,0),
                va='center',fontsize=9.5,color=INK2)
    ax.annotate(f"fires {cfg['cnt'][0]}–{cfg['cnt'][1]}   temp {cfg['temp'][0]}–{cfg['temp'][1]}"
                f"   world {cfg['dflt'][0]}–{cfg['dflt'][1]}",(1,y),textcoords='offset points',
                xytext=(0,15),fontsize=8.5,color=INK2,ha='left')
ax.axvline(13,color=C2,lw=2,ls='--')
ax.annotate('a single fixed world\n(1 fire, 300, -25)',(13,-0.62),ha='center',fontsize=9,
            color=C2,fontweight='bold')
ax.set_yticks(ys); ax.set_yticklabels([l for l,_ in COMBOS],fontsize=10.5)
ax.set_xlabel('% of the map survivable   (bar = 10th to 90th percentile across episodes, dot = median)')
ax.set_xlim(0,100); ax.set_ylim(-1.05,len(COMBOS)-.3)
ax.grid(True,axis='x',color=GRID,lw=.8); ax.set_axisbelow(True)
for s_ in ('top','right','left'): ax.spines[s_].set_visible(False)
ax.set_title('Each range produces a family of worlds, not one world',color=INK)
fig.suptitle('Campfire settings are ranges, sampled per episode',fontsize=13,fontweight='bold',y=.99)
fig.text(.5,-.01,'Top: six episodes drawn from combination B alone — the count, each fire\'s '
 'temperature and the world\'s baseline are all resampled. Circles mark the fires.',
 ha='center',color=INK2,fontsize=9)
fig.savefig('figH_ranges.png',dpi=140,bbox_inches='tight'); plt.close(fig)
print('figH written')

# ---------- FIG I : sit beside the fire, not on it ----------
SG_F, A_F, D_F = 0.7, 300.0, -25.0
def fire_field(A=A_F, sg=SG_F, dflt=D_F, fire=(5,5)):
    raw=np.full((H,W),float(dflt)); raw[fire]+=A; return gaussian_smooth(raw,sg)
def fire_prof(A=A_F, sg=SG_F, dflt=D_F):
    f=fire_field(A,sg,dflt); o={}
    for d in range(0,7):
        c=[f[r,cc] for r in range(H) for cc in range(W) if abs(r-5)+abs(cc-5)==d]
        if not c: continue
        amb=float(np.mean(c)); tr=body_traj([amb]*4000,k_ex=K_EX,k_loss=K_LOSS)
        i=int((np.abs(tr)>=DEATH).argmax()); o[d]=(amb,K_EX*amb/(K_EX+K_LOSS),None if i==0 else i)
    return o

P=fire_prof(); f=fire_field()
def burn_from_ring(P):
    T=K_EX*P[1][0]/(K_EX+K_LOSS)
    for k in range(30):
        T=T+K_EX*(P[0][0]-T)-K_LOSS*T
        if abs(T)>=DEATH: return k+1
    return None
BURN=burn_from_ring(P)
fig=plt.figure(figsize=(13.4,4.7)); gs=fig.add_gridspec(1,3,wspace=.30)

ax=fig.add_subplot(gs[0,0])
ds=sorted(P); eq=[P[d][1] for d in ds]
ax.axhspan(DEATH,200,color='#b02b2b',alpha=.13)
ax.axhspan(-200,-DEATH,color='#184f95',alpha=.13)
ax.plot(ds,eq,color=INK,lw=2.6,marker='o',ms=7,zorder=4)
ax.axhline(0,color=C3,lw=1.6,ls='--')
ax.annotate('set point',(6,1.6),ha='right',fontsize=8.5,color=C3,fontweight='bold')
ax.annotate(f'PAIN\ndead in {BURN}\nsteps',(0,P[0][1]),textcoords='offset points',xytext=(10,-6),
            fontsize=9.5,color='#b02b2b',fontweight='bold',va='center')
ax.annotate('comfort',(1,P[1][1]),textcoords='offset points',xytext=(12,4),
            fontsize=9.5,color='#0f7a55',fontweight='bold')
ax.annotate(f'lethal cold',(4,P[4][1]),textcoords='offset points',xytext=(6,-16),
            fontsize=9.5,color='#184f95',fontweight='bold')
ax.set_xlabel('Manhattan distance from the fire'); ax.set_ylabel('equilibrium body temperature')
ax.set_title('Beside the fire, not on it',color=INK)
ax.set_ylim(-30,max(eq)*1.18); ax.set_xlim(-.35,6.35)

ax=fig.add_subplot(gs[0,1])
for d,col,lab in [(0,'#b02b2b','d=0  on the fire'),(1,'#0ca30c','d=1  beside it'),
                  (2,'#6da7ec','d=2  cool'),(3,'#184f95','d=3  too far')]:
    T0=K_EX*P[1][0]/(K_EX+K_LOSS) if d==0 else 0.0
    tr=body_traj([P[d][0]]*70,T0=T0,k_ex=K_EX,k_loss=K_LOSS)
    ax.plot(tr,color=col,lw=2.2,label=lab)
ax.axhline(DEATH,color=INK,ls=':',lw=1.4); ax.axhline(-DEATH,color=INK,ls=':',lw=1.4)
ax.text(38,16.4,'heat death',ha='center',fontsize=8.5,color=INK)
ax.annotate(f'{BURN} steps',(BURN,DEATH),textcoords='offset points',xytext=(10,10),fontsize=9,color='#b02b2b',fontweight='bold')
ax.text(38,-18.6,'cold death',ha='center',fontsize=8.5,color=INK)
ax.set_xlabel('steps spent there  (first 70)'); ax.set_ylabel('body temperature')
ax.set_title('What happens if the agent stays\n(fire curve starts from the ring)',color=INK,fontsize=10)
ax.legend(frameon=False,fontsize=8.5,loc='upper right'); ax.set_ylim(-24,36); ax.set_xlim(0,70)

ax=fig.add_subplot(gs[0,2])
ax.imshow(f,cmap=DIV,norm=TwoSlopeNorm(0,-45,45))
for r in range(H):
    for c in range(W):
        dd=abs(r-5)+abs(c-5)
        if dd==1: ax.add_patch(Rectangle((c-.5,r-.5),1,1,fc='none',ec='#0ca30c',lw=2.4))
ax.add_patch(Rectangle((4.5,4.5),1,1,fc='none',ec='#b02b2b',lw=2.6))
ax.plot([5],[5],marker='*',ms=15,color='#fff3d6',zorder=5)
ax.set_title('red = pain, green = the comfort ring',color=INK); bare(ax)

for a in fig.axes[:2]:
    a.grid(True,color=GRID,lw=.8); a.set_axisbelow(True)
    for s_ in ('top','right'): a.spines[s_].set_visible(False)
fig.suptitle('Thermal pain without a pain sensor — the fire cell simply overshoots',
             fontsize=13,fontweight='bold',y=.99)
fig.text(.5,-.02,f'campfire {A_F:.0f}, sigma {SG_F}, world {D_F:.0f}. The fire cell sits at ambient '
 f'{P[0][0]:.0f}: walking onto it from the comfort ring kills in {BURN} steps. One cell away the body '
 f'settles at {P[1][1]:.1f} and is safe forever. No new internal state and no new sensor.',
 ha='center',color=INK2,fontsize=9)
fig.savefig('figI_pain.png',dpi=140,bbox_inches='tight'); plt.close(fig)
print('figI written')

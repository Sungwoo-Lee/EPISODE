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

DEFAULT, A_FIRE, SIGMA = -25.0, 300.0, 1.2
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
for Tf,col,lab in [(8,'#b02b2b','at the fire  (+8)'),(-12,'#e08a8a','d=2  (-12)'),
                   (-20,'#6da7ec','d=3  (-21)'),(-25,'#184f95','far field  (-25)')]:
    ax.plot(body_traj([Tf]*500,k_ex=K_EX,k_loss=K_LOSS),color=col,lw=2,label=lab)
ax.axhline(-DEATH,color=INK,ls=':',lw=1.3); ax.text(250,-17.5,'cold death',ha='center',fontsize=8.5,color=INK)
ax.set_xlabel('step'); ax.set_ylabel('body temperature'); ax.set_xlim(0,500); ax.set_ylim(-24,12)
ax.set_title('Body temp at each distance',color=INK); ax.legend(frameon=False,fontsize=8,loc='upper right')
ax=axes[1]
seq=[-25.0]*60+[8.0]*60+[-25.0]*60+[8.0]*60+[-25.0]*120
ax.plot(body_traj(seq,k_ex=K_EX,k_loss=K_LOSS),color=C1,lw=2.2)
for a,b in [(0,60),(120,180),(240,360)]: ax.axvspan(a,b,color=C1,alpha=.09)
ax.axhline(-DEATH,color=INK,ls=':',lw=1.3)
ax.set_xlabel('step'); ax.set_title('A foraging cycle  (shaded = away from fire)',color=INK)
ax.set_ylim(-24,12)
ax.annotate('dies on the third trip',(330,-16),fontsize=8.5,color=INK2)
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

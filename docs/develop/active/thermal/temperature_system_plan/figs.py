import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Rectangle, Circle
import numpy as np
from sim import *

SURF='#fcfcfb'; INK='#16181d'; INK2='#4e545e'; GRID='#e3e2de'
C1='#2a78d6'; C2='#eb6834'; C3='#1baf7a'; C4='#4a3aa7'
DIV=LinearSegmentedColormap.from_list('bt',['#184f95','#6da7ec','#f0efec','#e08a8a','#b02b2b'])
plt.rcParams.update({'figure.dpi':100,'figure.facecolor':SURF,'axes.facecolor':SURF,'savefig.facecolor':SURF,
 'text.color':INK,'axes.labelcolor':INK2,'xtick.color':INK2,'ytick.color':INK2,
 'axes.edgecolor':GRID,'font.size':10,'axes.titlesize':11,'axes.titleweight':'bold'})
def bare(ax):
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)

rng=np.random.default_rng(11)
OBJ=[(2,7,18.0),(3,7,18.0),(7,2,-14.0),(6,3,-14.0)]   # rock pair (warm), bush pair (cold)
st=build_field(rng,n_spots=2,spot_temp=20.0,spot_size=2,objects=OBJ,sigma=1.5)
M=max(abs(st['smoothed']).max(),abs(st['objects']).max())
norm=TwoSlopeNorm(0,-M,M)

# FIG A — construction pipeline
fig,axes=plt.subplots(1,4,figsize=(13.5,3.9))
for ax,(k,t) in zip(axes,[('fill','1. fill  default_temp'),('spots','2. + random spots'),
                          ('objects','3. + object stamps'),('smoothed','4. Gaussian smooth  sigma=1.5')]):
    ax.imshow(st[k],cmap=DIV,norm=norm); ax.set_title(t,color=INK,fontsize=10.5); bare(ax)
    if k in ('objects','smoothed'):
        for (r,c,tt) in OBJ:
            ax.add_patch(Rectangle((c-.5,r-.5),1,1,fc='none',ec=INK,lw=1.4,ls=':'))
fig.suptitle('Building the thermal field — stamps ADD, then one blur at the end',fontsize=12.5,fontweight='bold')
fig.text(.5,.02,'Dotted cells are object sources: a warm rock pair (+18) and a cold bush pair (-14). '
 'Additive stamping makes the result independent of spawn order.',ha='center',color=INK2,fontsize=9)
fig.tight_layout(rect=[0,.07,1,.90]); fig.savefig('figA_pipeline.png',dpi=140); plt.close(fig)

# FIG B — sigma sweep + navigability
sigmas=[0.0,0.5,1.0,1.5,3.0,6.0]
raw=st['objects']; MB=abs(raw).max(); nrm=TwoSlopeNorm(0,-MB,MB)   # ONE scale for all panels
fig=plt.figure(figsize=(12.6,6.6))
gs=fig.add_gridspec(2,6,height_ratios=[1.15,1],hspace=.45,wspace=.18)
for i,sg in enumerate(sigmas):
    ax=fig.add_subplot(gs[0,i]); f=gaussian_smooth(raw,sg)
    im=ax.imshow(f,cmap=DIV,norm=nrm)
    ax.set_title(f'sigma = {sg}',color=INK,fontsize=10.5)
    ax.set_xlabel(f'range {f.max()-f.min():.0f}',fontsize=8.5,color=INK2,labelpad=3)
    bare(ax)
cb=fig.colorbar(im,ax=[fig.axes[i] for i in range(6)],fraction=.016,pad=.012)
cb.set_label('cell temperature',fontsize=8.5,color=INK2); cb.ax.tick_params(labelsize=8,colors=INK2)
cb.outline.set_visible(False)
ss=np.linspace(0.01,6,50); gm=[]; dr=[]
for sg in ss:
    f=gaussian_smooth(raw,sg); gy,gx=np.gradient(f)
    gm.append(np.mean(np.hypot(gy,gx))); dr.append(f.max()-f.min())
axL=fig.add_subplot(gs[1,0:3]); axR=fig.add_subplot(gs[1,3:6])
for ax,y,lab in ((axL,gm,'mean |gradient| per cell'),(axR,dr,'field range (max - min)')):
    ax.plot(ss,y,color=C1,lw=2.2); ax.set_ylabel(lab,fontsize=9.5); ax.set_xlabel('smoothing sigma')
    ax.axvspan(1.0,2.0,color=C3,alpha=.14)
    ax.grid(True,color=GRID,lw=.8); ax.set_axisbelow(True); ax.set_xlim(0,6)
    for s_ in ('top','right'): ax.spines[s_].set_visible(False)
axL.set_title('How much local slope survives',color=INK,fontsize=10.5)
axR.set_title('How much contrast survives',color=INK,fontsize=10.5)
axL.annotate('usable band 1.0-2.0',(1.5,max(gm)*.72),ha='center',fontsize=9,
             color='#0f7a55',fontweight='bold')
fig.suptitle('Smoothing sigma sets how navigable the field is',fontsize=13,fontweight='bold',y=.98)
fig.text(.5,.005,'All six panels share one colour scale, so the fade at high sigma is a real loss of '
 'contrast, not a rescaling. sigma=0 leaves cliffs with no climbable slope; by sigma=6 the 10x10 grid '
 'is nearly uniform and the field carries almost no information.',ha='center',color=INK2,fontsize=9)
fig.savefig('figB_sigma.png',dpi=140,bbox_inches='tight'); plt.close(fig)

# FIG C — body temperature dynamics
fig,axes=plt.subplots(1,3,figsize=(13.5,4.2))
ax=axes[0]
for Tf,col in [(20,'#b02b2b'),(10,'#e08a8a'),(0,'#8a8f97'),(-10,'#6da7ec'),(-20,'#184f95')]:
    tr=body_traj([Tf]*500); ax.plot(tr,color=col,lw=2,label=f'ambient {Tf:+d}')
ax.axhline(15,color=INK,ls=':',lw=1.3); ax.axhline(-15,color=INK,ls=':',lw=1.3)
ax.text(250,15.9,'death threshold',ha='center',fontsize=8.5,color=INK); ax.text(250,-17.2,'death threshold',ha='center',fontsize=8.5,color=INK)
ax.set_xlabel('step'); ax.set_ylabel('body temperature'); ax.set_xlim(0,500); ax.set_ylim(-21,19)
ax.set_title('Body temp under constant ambient',color=INK)
ax.legend(frameon=False,fontsize=8,loc='center right',bbox_to_anchor=(1.0,.45))
ax=axes[1]
for kx,col in [(0.01,C4),(0.02,C1),(0.04,C3),(0.08,C2)]:
    tr=body_traj([20.0]*300,k_ex=kx); ax.plot(tr,color=col,lw=2,label=f'k_exchange={kx}')
ax.axhline(15,color=INK,ls=':',lw=1.3)
ax.set_xlabel('step'); ax.set_title('Effect of k_exchange  (ambient +20)',color=INK)
ax.legend(frameon=False,fontsize=8.5,loc='lower right')
ax=axes[2]
ks=np.linspace(0.005,0.12,120); tt=[]
for kx in ks:
    tr=body_traj([20.0]*5000,k_ex=kx); i=np.argmax(tr>=15.0); tt.append(i if i>0 else np.nan)
tt=np.array(tt,float); k_crit=0.01*15/(20-15)
ax.axvspan(ks[0],k_crit,color='#8a8f97',alpha=.16)
ax.plot(ks,tt,color=C1,lw=2.2)
ax.axvline(0.04,color=C3,lw=1.8)
ax.plot([0.04],[55],marker='o',ms=7,color=C3,zorder=5)
ax.annotate('proposed 0.04\n55 steps',(0.04,55),textcoords='offset points',xytext=(14,26),
            fontsize=9,color='#0f7a55',fontweight='bold')
ax.text((ks[0]+k_crit)/2,tt[~np.isnan(tt)].max()*.55,'a +20 cell\nnever kills',ha='center',
        fontsize=8.8,color='#5c6068',fontweight='bold')
ax.set_xlabel('k_exchange'); ax.set_ylabel('steps to heat death in a +20 cell')
ax.set_xlim(ks[0],ks[-1]); ax.set_ylim(0,tt[~np.isnan(tt)].max()*1.25)
ax.set_title('Choosing k_exchange   (k_loss = 0.01)',color=INK)
for a in axes:
    a.grid(True,color=GRID,lw=.8); a.set_axisbelow(True)
    for s in ('top','right'): a.spines[s].set_visible(False)
fig.suptitle('Body temperature is a first-order lag toward local ambient',fontsize=12.5,fontweight='bold')
fig.tight_layout(rect=[0,.02,1,.92]); fig.savefig('figC_body.png',dpi=140); plt.close(fig)

# FIG D — rendering proposal
fig,axes=plt.subplots(1,2,figsize=(11,5.0))
ents={'food':[(1,2),(8,6)],'pred':[(4,8)],'bush':[(7,2),(6,3)],'rock':[(2,7),(3,7)]}
COLS={'food':'#0ca30c','pred':'#d03b3b','bush':'#1baf7a','rock':'#7a7168'}
agent=(5,4)
for ax,show_temp in zip(axes,[False,True]):
    if show_temp:
        ax.imshow(st['smoothed'],cmap=DIV,norm=norm,alpha=.85)
    else:
        ax.imshow(np.zeros((H,W)),cmap='Greys',vmin=0,vmax=1)
    for r in range(H+1): ax.axhline(r-.5,color=GRID,lw=.6)
    for c in range(W+1): ax.axvline(c-.5,color=GRID,lw=.6)
    for k,ps in ents.items():
        for (r,c) in ps:
            ax.add_patch(Circle((c,r),.30,fc=COLS[k],ec=SURF,lw=1.4,zorder=3))
    ax.add_patch(Circle((agent[1],agent[0]),.34,fc=INK,ec=SURF,lw=1.6,zorder=4))
    if show_temp:
        for dr,dc in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]:
            ax.add_patch(Rectangle((agent[1]+dc-.5,agent[0]+dr-.5),1,1,fc='none',ec='#111',lw=1.7,zorder=5))
    ax.set_xlim(-.5,W-.5); ax.set_ylim(H-.5,-.5); bare(ax)
    ax.set_title('current render' if not show_temp else 'proposed: temperature underlay + read cells',
                 color=INK,fontsize=11)
fig.suptitle('Rendering — temperature as a background layer, entities unchanged on top',
             fontsize=12.5,fontweight='bold')
fig.text(.5,.03,'The thermal field is the only new pixel data. Black outline marks the five cells the '
 'thermoceptor reads. Entity markers keep their existing colours and z-order.',ha='center',color=INK2,fontsize=9)
fig.tight_layout(rect=[0,.08,1,.92]); fig.savefig('figD_render.png',dpi=140); plt.close(fig)
print('ok')

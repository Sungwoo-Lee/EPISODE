---
title: "Events as Triggers for Behavioral Diversity (event-triggered LoRA hypernetwork)"
slug: buchi_2026_events
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_held_unreviewed.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 2. Büchi et al. — Events as Triggers

**Full title:** *Events as Triggers for Behavioral Diversity in Multi-Agent Reinforcement Learning*
**PDF:** `docs/project/references/modulation_in_rl/sources/Büchi et al. 2026 - Events as triggers - event-triggered LoRA hypernetwork (preprint).pdf`
**Venue as printed inside the PDF (page 1, verified):** the single word **"Preprint."** —
there is no venue. Left-margin stamp: `arXiv:2605.12388v2 [cs.MA] 13 May 2026`. So:
**no venue, arXiv preprint, v2**. Authors: Hannes Büchi, Manon Flageat\*, Eduardo
Sebastián\* (\*equal contribution), Amanda Prorok — Department of Computer Science and
Technology, University of Cambridge. Funded by ERC 949940 (gAIa), Leverhulme, EPSRC
INFORMED-AI.

**The method has no name.** It is called "our framework" throughout; the code link is
an anonymised `anonymous.4open.science/r/hyperscale-48D6/` URL, which is the only place
a candidate name ("hyperscale") appears. Note the mismatch: the PDF names its authors
but links an *anonymised* repository, so this v2 appears to be a de-anonymised revision
of a blind submission. When citing, call it "Büchi et al.'s event-driven framework"
rather than inventing a name.

### 2.1 What the paper is about, in plain words

Teams of agents need to change what they are doing at specific moments — a defender
pushes forward the instant possession changes, the rest of a search team spreads out
the instant one drone's battery dies. Existing methods for making agents behave
differently from each other tie a behaviour to an **agent** and then fix it: either
for the whole episode, or on a fixed clock (every timestep, every $k$ steps). Neither
matches "at the right moment".

This paper's proposal is to trigger behaviour changes on **events** — designated
changes in the world state, like a door opening or a teammate disappearing. It does
this with a generator network that, whenever an event fires, writes out a **small
weight correction** for each agent. The correction is low-rank ("LoRA"): instead of a
full replacement weight matrix it is a product of two thin matrices, so it is cheap to
emit. Between events the correction is held fixed, so the policy is a stable network
most of the time.

The second contribution is a diversity measure, **NMD**, that asks "how different are
the behaviours the team is currently running?" without asking *which agent* is running
which — because in this framework behaviours move between agents. A scalar $\alpha$
then rescales all the corrections so that the measured diversity hits a requested
target exactly.

**Headline verdict.** This is the paper the wider report needs for the **low-rank rung**
of the capacity spectrum, and it earns the slot: it is explicitly positioned as "a
computationally efficient alternative to full policy regeneration", it has the corpus's
only direct **rank sweep**, and it has a clean ablation of *when* the generator is
queried. Two things make it more valuable than its preprint status suggests. First, it
is a **direct empirical counter-example to HyperMARL's headline**: its generator reads
the agents' observations — precisely HyperMARL's `w/o GD` configuration — and it beats
HyperMARL on all four shared benchmarks. Second, its **rank ablation finds no effect
across a 32× range** ($r = 2 \to 64$), which is the only measurement in the corpus
bearing directly on how much adapter capacity is actually needed. Against that: no
venue, five seeds, several claims asserted rather than tested, one paragraph that
misdescribes its own figure, and an algebra slip in a corollary's proof.

### 2.2 Direct answers to the required questions

| Question | Answer |
|---|---|
| **Conditioning signal** | Three things, jointly, into one transformer generator $g_\theta$: (i) **one token per agent formed from that agent's local observation** $o_{i,t}$; (ii) the **event encoding** $e_t$ for the most recent event $\xi_t$; (iii) the **global target diversity scalar** `NMD_des`. So the generator reads (a) the raw observation stream, (b) a discrete event symbol, and (c) a user-set control knob. **It is centralised** — the Limitations section concedes it "requires access to the observations from all agents to assign behaviors". |
| **What is generated / modulated** | A **LoRA pair** $(C_m, D_m)$ per agent, with $C_m \in \mathbb{R}^{r\times d}$, $D_m \in \mathbb{R}^{d_a \times r}$, $r \ll d$, $r = 8$ in all experiments. Applied to **the final linear layer of the policy only** — one site, one layer, actor side. The **critic is not modulated**: MAPPO's critic is a separate `[128,128]` network with no adapter. The shared policy backbone $W_{\text{shared}}$ is `[128,128]`. Index $m$ rather than $i$ is deliberate: the generator may emit the *same* pair for several agents, because behaviours are not owned by agents. |
| **The operator, and where it sits on the capacity spectrum** | **Low-rank additive residual with a global scalar gain** — the rung between FiLM and full weight generation, which is exactly what the report needed populated. $$z_m(o_t) = W_{\text{shared}}\,\phi(o_t) \;+\; \alpha\, D_m C_m\, \phi(o_t)$$ Note this contains **two** distinguishable mechanisms: a *low-rank weight delta* $D_m C_m$ (rank 8, generated) and a *scalar gain* $\alpha$ (computed, not generated — see below). It is **additive in pre-activation space, not multiplicative per channel**, so it is not FiLM: there is no $\gamma \odot h$ term and no per-channel parameterisation. But it is also decisively **not full weight generation** — the backbone is shared and only the deviation is emitted, "keeping the hypernetwork output small and the solution memory efficient". |
| **Query frequency** | **Event-triggered.** $g_\theta$ is queried "only when an event fires (and once at initialization); between events, the pair is held fixed." This is presented as a third option between HyperMARL's episode-initial generation ("static brittleness") and CASH's per-timestep generation ("the cost and instability of per-step regeneration"). **This axis — how often the generator runs — is separable from what it reads, and this paper is the corpus's first to treat it as a design variable.** |
| **RL algorithm** | **MAPPO** (on-policy, centralised critic). Adam, $\gamma = 0.99$, GAE $\lambda = 0.95$, clip 0.2, entropy coef 0.01, value coef 0.5, max grad norm 0.5, LR $6\times10^{-4}$, 128 parallel environments, 8 minibatches, $10^7$ total steps ($150\times10^6$ for Football). |
| **Environments** | Six, **all in VMAS**. Four established diversity benchmarks: **Reverse Transport** (collective package pushing), **Navigation** (LiDAR-limited exploration), **Dispersion** (reach $M$ targets from a shared spawn), **Football** (3 agents vs a scripted heuristic team). Two purpose-built: **Pressure Plate** (3 agents, 2 plates, a locked door — requires a strictly sequential three-phase strategy) and **Wind Flocking** (a larger agent must shield a smaller one from wind). |
| **Baselines** | Four: **HyperMARL** (episode-wise allocation, hypernetwork on agent IDs — i.e. paper §1 of this document); **CASH** (Capability-Aware Shared Hypernetworks, CoRL 2025 — per-timestep allocation, hypernetwork on capabilities or IDs); **DiCo** (Diversity Control — per-agent deviation scaled to hit a target SND, with the target grid-searched over $\{0.1, 0.2, 0.5, 0.9, 1.0, 1.1, 1.5, 2.0\}$ per task and the best reported); **PS** (full parameter sharing, no allocation). |
| **Seed counts** | **5 seeds everywhere.** Results are box plots over 5 seeds, evaluated at "the best-performing checkpoints saved during the training process" — i.e. **best-checkpoint selection, not final performance**, which inflates every method's numbers including the baselines. Total compute: ~1000 GPU-hours on one RTX 2080 Ti. |
| **Reported instabilities / failure modes** | (a) **The event trigger is all-or-nothing**: the single-query ablation scores **0 %** on Pressure Plate against 98.5 % for the full method. (b) **CASH is reported as unstable** — "shaky" learning curves, and "in some independent runs, fails to converge to a competitive reward", attributed by the authors to per-timestep hypernetwork re-querying making the policy "highly sensitive to minor fluctuations in the hypernetwork's output". This is an *attribution about a baseline*, not a controlled test. (c) Three self-declared limitations: behaviour expressivity is bounded by the LoRA representation; **events must be hand-defined with domain knowledge**; the architecture is centralised. |

### 2.3 Headline numbers

The main results figure (Fig. 2) is a **raster image with no printed values**, as are
Figs. 3, 4a, 4b, 6 and 7. Only Table 4c carries numbers. Values below marked
**[digitized]** were read off high-resolution renderings of the figure images; box-plot
medians are given to the nearest half-percent and should be treated as ±1 %.

**Q1 — completion rate (%) across the four shared benchmarks, median of 5 seeds [digitized from Fig. 2].**

| Task | **Ours** | HyperMARL | CASH | DiCo | PS |
|---|---|---|---|---|---|
| Reverse Transport | **100** | 100 | ~33 (box 33–100) | 100 | ~33 |
| Navigation | **96** | 69 | 95.5 | 91 | 84.5 |
| Dispersion | **99** | 65.5 | 33 | 85 | 50.5 |
| Football | **~98** | **0** | **0** | **0** | **0** |

**Football is the headline**: every baseline sits at zero completion while the proposed
method sits near 100. The authors attribute this to the task's reliance on event-driven
role transitions — possession changes, ball proximity, opponent positioning — "which
static or scheduled allocations cannot track". Whatever the mechanism, a 0-vs-98 gap
against four baselines is the largest single result in this paper and one of the
largest in the corpus.

**Q3 — Pressure Plate completion rate (%), median of 5 seeds [digitized from Fig. 4a].**

| **Ours** | Ours **SQ** (single query — event re-querying removed) | HyperMARL | CASH | DiCo | PS |
|---|---|---|---|---|---|
| **98.5** (whiskers 96–100) | **0** | 0 | 0 | 0 | 0 |

This is the paper's best-designed comparison and its most useful single number for the
report. `Ours SQ` is the **same architecture, same LoRA, same generator, same
conditioning inputs** — the only change is that the generator is queried once at
initialisation instead of at every event. That change costs **all** of the performance.
The mechanism is diagnosed concretely: with a static assignment "the final agent
remain[s] stuck behind the door".

**Q4 — robustness to unseen mid-episode agent removal (Table 4c, the paper's only numeric table).**
Median completion rate with $+(Q_3 - M) / -(M - Q_1)$:

| Environment | Agent removal | Completion rate (%) |
|---|---|---|
| Pressure Plate | No | 98.4 $^{+1.4}_{-0.8}$ |
| Pressure Plate | **Yes** | **81.2** $^{+0.9}_{-0.2}$ |
| Football | No | 98.2 $^{+1.0}_{-0.8}$ |
| Football | **Yes** | **88.6** $^{+6.6}_{-0.7}$ |

The authors' framing is careful and correct: "neither perturbation pushes performance
into the regime occupied by the baselines in Section 5.2". On Football that regime is
0 %, so 88.6 % after losing an agent mid-episode is a real result.

**Q2 — zero-shot generalisation (Fig. 3, no numbers, no values digitizable at useful
precision).** Three axes: agent count, physical capability (LiDAR range / speed /
force), and target diversity `NMD_des`. Claimed stable across all three, including
out-of-distribution ranges, and "stable across roughly two order[s] of magnitude of NMD
values". **HyperMARL is excluded from the agent-count axis because "its architecture
cannot accommodate changes in team size"** — a structural consequence of the one-hot /
per-agent-embedding conditioner that is worth carrying forward as a general property
of identity-conditioned generators.

**LoRA rank ablation (Fig. 7, App. D.2) — the corpus's only direct capacity sweep.**
Ranks $r \in \{2, 4, 8, 16, 32, 64\}$ on Navigation, 5 seeds each, mean episode reward
over 300 logged training steps. **All six ranks converge to the same band, roughly
0.010–0.012 average reward, with heavily overlapping confidence intervals and no
visible ordering** [digitized from Fig. 7]. The only differences are in late-training
noise, where rank 32 shows the widest band including an excursion toward 0.

The text says $r = 8$ "proved to be the 'sweet spot' for our architecture, providing
sufficient expressivity while maintaining the stability of the hypernetwork during
training." **The figure does not show this.** It shows rank to be immaterial over a 32×
range on this task. That is a *more* interesting finding than the one claimed, and it
should be recorded as such: **on a VMAS navigation task, adapter capacity between rank
2 and rank 64 is not the binding constraint.** Caveats — one task only, average reward
rather than completion rate, and a $y$-range of 0 to 0.012 in which absolute
differences are tiny by construction.

### 2.4 The finding that matters most: this paper contradicts HyperMARL, and the reconciliation is *query frequency*

Set the two papers side by side on the exact axis the report cares about.

| | HyperMARL (§1) | **Büchi et al.** | CASH (baseline in both) |
|---|---|---|---|
| Generator reads | agent identity **only** | **local observations** + event + diversity target | capabilities or agent ID |
| Generator queried | **once per training iteration** (Alg. 1) | **only when an event fires** | **every timestep** |
| Emits | all target weights | rank-8 LoRA pair for one layer | agent-specific weights |
| Reported outcome | works; adding $o_t$ to the generator (`w/o GD`) **degrades on both tested environments** | works; **beats HyperMARL on all four shared benchmarks** | "shaky"; "in some independent runs, fails to converge" |

HyperMARL's `w/o GD` ablation and Büchi's *main method* occupy the same cell on the
"what does the generator read" axis — the observation enters the generator while the
generated network also reads it — and reach opposite verdicts. Taken at face value that
is a straight contradiction, and it is the single most useful thing this paper
contributes to the report, because the corpus previously had HyperMARL's `w/o GD`
standing unopposed.

**The reconciliation the two papers jointly suggest is that the harmful variable is not
*whether* the generator reads the observation but *how often* it re-reads it.**
HyperMARL's `w/o GD` conditions on $[o_t, e_i]$, which forces regeneration at **every
timestep** (this is the confound identified in §1.4(d) above). Büchi's generator reads
observations too, but only at **event boundaries** — a handful of times per episode —
and holds the adapter fixed in between, so the policy is a static network for most of
the rollout. And Büchi independently names per-step regeneration as the failure
mechanism for CASH, in language that reads as a direct description of what `w/o GD`
does: "the resulting policy can be highly sensitive to minor fluctuations in the
hypernetwork's output."

So the corpus now supports a sharper statement than "don't let the generator see the
observation":

> **Generator query frequency is a design variable in its own right, and the evidence
> across three architectures orders it: once-per-episode is brittle (Büchi's `SQ`
> ablation: 0 %), once-per-event works, once-per-timestep is reported unstable twice
> independently (HyperMARL `w/o GD`; CASH).**

Four caveats before this is used:
1. **The comparison is not capacity-matched.** Büchi's method uses a 2-block/2-head
   transformer generator with embedding 64 and MLP hidden 256, over a `[128,128]`
   backbone; its HyperMARL baseline is configured with hypernetwork width 64, agent
   networks `[64,64]`, embedding dim 8 (Table 1). The winner has more parameters
   everywhere. HyperMARL's own paper ran a matched-parameter control against FuPS;
   Büchi runs none against HyperMARL.
2. **The frequency ordering is not ablated within one architecture.** Büchi ablates
   *fewer* queries (`SQ`) but never *more* (per-step). The "cost and instability of
   per-step regeneration" claim is supported only by a cross-architecture baseline
   comparison and a post-hoc attribution. **Nobody in this corpus has run the clean
   experiment: one architecture, one conditioner, query frequency swept.**
3. **The tasks differ.** HyperMARL's `w/o GD` was tested on 17-agent Humanoid and
   Dispersion; Büchi's are VMAS 2D tasks with three to eight agents. Both include a
   Dispersion, but they are different implementations with different observation spaces.
4. **Best-checkpoint selection.** Büchi evaluates "the best-performing checkpoints
   saved during the training process" for all methods. This is applied uniformly, so
   it does not obviously favour one method, but it means none of these numbers are
   end-of-training numbers.

### 2.5 Phase 1 — foundational overview

**The problem.** A team should change roles *when something happens*, not on a
schedule and not according to a fixed assignment made at the start. Existing methods do
one or the other.

**The idea.** Treat the set of useful behaviours as belonging to the *task*, not to the
agents — a "behaviour manifold" the team draws from. Nobody is permanently the scout.
When a designated **event** occurs (a door opens, a teammate is lost, the requested
diversity changes), a generator network re-reads the situation and hands each agent a
small weight patch that instantiates whichever behaviour is now appropriate.

**Why the patch is small.** Emitting a full weight matrix per agent per event would be
expensive and, the authors argue, harder to optimise. Instead the generator emits two
thin matrices whose product is a low-rank correction added to the last layer of a
shared policy. The shared part learns what the task always requires; the patch encodes
only the difference.

**Controlling how different the agents are.** A measure called NMD averages the
distance between the action distributions of any two behaviours currently running,
without reference to who is running them. A single number $\alpha$ then rescales all
the patches so the measured diversity equals a requested target — and because the patch
enters the network linearly, the rescaling is exact rather than approximate.

**Key findings.**
- Wins on all four established benchmarks; on the hardest one, Football, all four
  baselines score zero completion and this method scores ~98 %.
- The only method that solves a task requiring behaviours to be handed off in sequence
  — and it does so **without any memory mechanism**, which is a genuinely surprising
  result: the sequencing is carried by the event trigger rather than by an RNN state.
- Removing the event trigger (querying once at the start instead) drops that task from
  98.5 % to 0 %.
- Adapter rank makes no measurable difference from 2 to 64.

**Initial takeaway.** The interesting variable in this paper is not the operator — a
low-rank additive patch — but the **schedule**. Almost all of the demonstrated benefit
traces to *when* the generator is consulted, not to what it emits or how expressive
that emission is. The rank sweep says the "how expressive" axis is flat; the single-query
ablation says the "when" axis is the difference between 98.5 % and 0 %.

### 2.6 Phase 2 — graduate-level deep dive

**Event-augmented POMG.** A standard partially observable Markov game
$\mathcal{M} = \langle N, S, A, O, P, \Omega, R, \gamma, B\rangle$ is augmented with a
discrete event space $\Xi$ and an event-detection map
$E : S \to \Xi \cup \{\varnothing\}$, giving
$\mathcal{M} = \langle N, S, A, O, P, \Omega, R, \gamma, B, \Xi, E\rangle$. $B$ is the
**behaviour manifold**: the space of admissible policies $\pi : O \to \mathcal{P}(A)$
the task supports. Crucially $B$ is defined as a property of the *task*, not given a
priori, and learning it is the paper's object. An event induces a non-stationary
transition $(s_t, N_t, b_t) \xrightarrow{\;\xi_t\;} (s_{t+1}, N_{t+1}, b_{t+1})$ where
$b_t = (\pi_{1,t}, \dots, \pi_{|N_t|,t}) \in B^{|N_t|}$ — note that the *team's
behaviour assignment* is part of the state being transitioned, which is what makes
"the same agent, a different behaviour" expressible at all.

One modelling choice deserves flagging: capability descriptors are folded **into the
observation vector** $o_i$ rather than treated as separate quantities, "to emphasize
that our focus is on behavioral diversity, in which agents display different action
distributions given identical inputs, rather than physical diversity". This is what
makes the diversity claim non-trivial — the agents are not different because their
inputs differ.

**Neural Manifold Diversity (Def. 1).**

$$\mathrm{NMD}(B, O) = \int_B \int_B \int_O W_2\big(\pi_m(o), \pi_n(o)\big)\, p(o)\, \mathrm{d}o\; p(\pi_m)\,\mathrm{d}\pi_m\; p(\pi_n)\,\mathrm{d}\pi_n,$$

with $W_2$ the 2-Wasserstein distance between action distributions. Estimator over a
finite behaviour set $\{\pi_m\}_{m=1}^{B}$ and episodic observations $O_{\text{ep}}$:

$$\widehat{\mathrm{NMD}}\big(\{\pi_m\}_{m=1}^{B}\big) = \frac{2}{B(B-1)\,|O_{\text{ep}}|} \sum_{m=1}^{B}\sum_{n=m+1}^{B}\sum_{o \in O_{\text{ep}}} W_2\big(\pi_m(o), \pi_n(o)\big).$$

In the implementation $\{\pi_m\}$ is **the set of behaviours in a parallel batch of
environments** — with 128 parallel environments, $B$ is large. The structural
difference from SND (Bettini et al., JMLR 2025), which this generalises, is stated
sharply: "the most important aspect of NMD is what is absent from it: agent indices."
SND sums over agent pairs; NMD sums over behaviour pairs. That is what keeps it
well-defined when behaviours are transient and migrate between agents.

**Proposition 2 (NMD's kernel is a metric).** For
$d(\pi_m, \pi_n) := \mathbb{E}_{o\sim p(o)}[W_2(\pi_m(o), \pi_n(o))]$, $d$ is a
pseudometric on $B$, and a metric when policies are distinguishable on $\mathrm{supp}\,p(o)$.
The proof (App. B.2) is a routine lift of $W_2$'s metric axioms through an expectation:
non-negativity and symmetry are pointwise and preserved by $\mathbb{E}$; the triangle
inequality is pointwise plus linearity and monotonicity of expectation; the identity
direction gives $\pi_m = \pi_n$ only $p$-almost-everywhere, hence pseudometric, upgraded
to metric under a separation assumption. Corollary 5: $\mathrm{NMD}(B) = 0 \iff p(\pi)$
concentrates on a single behaviour.

**The architecture.** Let $g_\theta$ be a transformer hypernetwork. It ingests one token
per agent from $o_{i,t}$, the event encoding $e_t$, and `NMD_des`, and emits
$(C_m, D_m)$. With $\phi(o_t)$ the penultimate feature of the shared policy, the
pre-activation of behaviour $m$ is

$$z_m(o_t) = W_{\text{shared}}\,\phi(o_t) + \alpha\, D_m C_m\, \phi(o_t). \tag{3}$$

The action distribution is $\pi_m(o_t) = \sigma(z_m(o_t))$ with $\sigma$ a squashed
Gaussian for continuous control. The three stated design reasons are worth separating,
because only one of them is empirically tested:
1. *Low rank stabilises optimisation relative to dense matrices, and shrinks the
   generator's output dimension.* **Not tested against a dense-generation control.** The
   rank sweep (App. D.2) varies $r$ within the low-rank family; it never includes
   $r = d$ or a dense baseline. So "low-rank beats dense" is **asserted**.
2. *Final-layer placement makes the heterogeneous component enter linearly in
   $\phi(o_t)$.* This is not an empirical claim but a **precondition for the theory** —
   see below. Not ablated (no alternative injection site is tried).
3. *The shared backbone accumulates task-general representations while $(C_m, D_m)$
   encodes only the deviation.* Interpretive; not measured.

**Diversity control (Eq. 4).** Write each behaviour as a shared term plus a deviation
$u_m(o_t) := D_m C_m \phi(o_t)$. Set

$$\alpha = \frac{\mathrm{NMD}_{\text{des}}}{\widehat{\mathrm{NMD}}\big(\{u_m(o_t)\}_{m=1}^{B}\big)}.$$

Because the deviation enters Eq. (3) **linearly**, scaling every $u_m$ by $\alpha$
scales the pairwise behavioural distance by exactly $\alpha$, so the realised diversity
equals $\mathrm{NMD}_{\text{des}}$ **by construction** rather than by optimisation. This
is the technical payoff of final-layer placement: "any nonlinearity between the LoRA
update and the policy mean would forfeit this reduction." It generalises DiCo's
$\pi_i(o) = \pi_h(o) + \lambda\,\pi_{h,i}(o)$ from a fixed indexed agent set to a
time-varying behaviour set.

Note what $\alpha$ *is*, mechanistically: a **single global scalar gain on the
modulation path, recomputed per batch as a normalisation ratio.** It is not generated
by the hypernetwork and it is not per-channel. Structurally it is a diversity-targeting
automatic gain control — closer in spirit to a normalisation layer than to FiLM's
$\gamma$.

**Lemma 6 (why $W_2$ collapses to a Euclidean distance).** Under (A3) — Gaussian
policies $\pi_m(\cdot\mid o) = \mathcal{N}(\mu_m(o), \Sigma)$ with $\Sigma$ shared
across behaviours and independent of $o$ — the Olkin–Pukelsheim formula

$$W_2^2\big(\mathcal{N}(\mu_m,\Sigma_m), \mathcal{N}(\mu_n,\Sigma_n)\big) = \lVert \mu_m - \mu_n\rVert_2^2 + \operatorname{tr}\!\Big(\Sigma_m + \Sigma_n - 2(\Sigma_m^{1/2}\Sigma_n\Sigma_m^{1/2})^{1/2}\Big)$$

has a vanishing trace term, since $\Sigma_m = \Sigma_n = \Sigma \succ 0$ gives
$\Sigma^{1/2}\Sigma\Sigma^{1/2} = \Sigma^2$ and $(\Sigma^2)^{1/2} = \Sigma$, so the
bracket is $2\Sigma - 2\Sigma = 0$. Hence $W_2(\pi_m, \pi_n) = \lVert\mu_m - \mu_n\rVert_2$.
Substituting $\mu_m - \mu_n = \alpha(u_m - u_n)$ from (A4),

$$\widehat{\mathrm{NMD}} = \frac{2\alpha}{B(B-1)|O_{\text{ep}}|}\sum_{i<j}\sum_{o \in O_{\text{ep}}} \lVert u_m - u_n\rVert_2, \tag{5}$$

which is **homogeneous of degree 1** in the deviations. That homogeneity is the engine
of the next result.

**Theorem 3 (diversity control as a gradient projection).**

$$\nabla_{u_m} R = \alpha\, P_{u_m} (\nabla_{z_m} R)^\top, \qquad P_{u_m} = I - \frac{u_m \otimes \nabla_{u_m}\widehat{\mathrm{NMD}}}{\widehat{\mathrm{NMD}}},$$

with $P_{u_m}$ idempotent. Derivation, in the paper's three steps:

*Step 1.* $z_m = W_{\text{shared}}\phi + \alpha u_m$, and $\alpha$ itself depends on
$u_m$ through $\widehat{\mathrm{NMD}}$, so

$$\frac{\partial z_m}{\partial u_m} = \alpha I + u_m \otimes \nabla_{u_m}\alpha.$$

By the quotient rule on $\alpha = \mathrm{NMD}_{\text{des}}/\widehat{\mathrm{NMD}}$,

$$\nabla_{u_m}\alpha = -\frac{\mathrm{NMD}_{\text{des}}}{\widehat{\mathrm{NMD}}^{\,2}}\nabla_{u_m}\widehat{\mathrm{NMD}} = -\frac{\alpha}{\widehat{\mathrm{NMD}}}\nabla_{u_m}\widehat{\mathrm{NMD}},$$

giving $\partial z_m/\partial u_m = \alpha\big(I - \widehat{\mathrm{NMD}}^{-1} u_m \otimes \nabla_{u_m}\widehat{\mathrm{NMD}}\big) = \alpha P_{u_m}$.

*Step 2.* Chain rule: $\nabla_{u_m} R = (\partial z_m/\partial u_m)^\top \nabla_{z_m} R = \alpha P_{u_m}^\top \nabla_{z_m} R$.

*Step 3 (idempotency).* Write $v := \nabla_{u_m}\widehat{\mathrm{NMD}}$, $N := \widehat{\mathrm{NMD}}$.
By Eq. (5), $\widehat{\mathrm{NMD}}$ is positively homogeneous of degree 1 in $u_m$, so
**Euler's homogeneous function theorem** gives

$$u_m^\top \nabla_{u_m}\widehat{\mathrm{NMD}} = \widehat{\mathrm{NMD}}, \quad\text{i.e.}\quad v^\top u_m = N. \tag{6}$$

Then

$$P_{u_m}^2 = \Big(I - \tfrac{u_m v^\top}{N}\Big)^2 = I - \frac{2 u_m v^\top}{N} + \frac{u_m (v^\top u_m) v^\top}{N^2} = I - \frac{2u_m v^\top}{N} + \frac{u_m v^\top}{N} = I - \frac{u_m v^\top}{N} = P_{u_m}.$$

The interpretation the paper draws is the right one and is worth quoting: diversity
control "does not enter as an external regularizer, but as a projector on the
reward-maximizing gradient: any component of $\nabla_{z_m} R$ that would alter
$\widehat{\mathrm{NMD}}$ is filtered out before the LoRA parameters are updated." No
auxiliary loss, no trust region, no coefficient to tune against the return.

**Three honest problems with the theory, in ascending order of seriousness.**

*(i) A dropped transpose.* Step 2 produces $P_{u_m}^\top$; the paper then writes "Because
$P_{u_m}$ is symmetric in the dyadic structure that matters for the projection identity
below … we drop the transpose for notational convenience." But
$P_{u_m} = I - u_m v^\top / N$ is symmetric only when $u_m \parallel v$, which is not
true in general. An idempotent non-symmetric matrix is an **oblique** projection, not an
orthogonal one — it still annihilates the offending direction, but it does not do so by
orthogonal removal, and $P^\top \ne P$ means Step 2's result and Theorem 3's statement
are not literally the same object. The qualitative conclusion survives; the equation as
printed does not.

*(ii) An algebra slip in Corollary 4, which changes the displayed limit.* Corollary 4's
dominant-deviation regime writes $u_m = t\hat u_m$, $t \to \infty$, and asserts

$$\widehat{\mathrm{NMD}} = \frac{c(B-1)}{B(B-1)/2}t + O(1) = \frac{2c}{B}t + O(1), \qquad \nabla_{u_m}\widehat{\mathrm{NMD}} = c(B-1)\hat u_m + O(1/t),$$

concluding $P_{u_m} \to I - \tfrac{B(B-1)}{2}\hat u_m \hat u_m^\top$ and calling this
"the orthogonal projector onto $\hat u_m^\perp$". **It is not**, for any $B > 2$: the
orthogonal projector onto $\hat u^\perp$ is $I - \hat u \hat u^\top$, and
$I - c\,\hat u\hat u^\top$ satisfies $(I - c\hat u\hat u^\top)^2 = I - (2c - c^2)\hat u\hat u^\top$,
which equals itself only for $c \in \{0, 1\}$. With $B$ = the number of parallel
environments = 128, the printed coefficient is $B(B-1)/2 = 8128$, an operator that
*reflects and amplifies* along $\hat u$ rather than projecting.

The error is locatable: the normalisation factor $2/(B(B-1))$ is retained in
$\widehat{\mathrm{NMD}}$ but **dropped from $\nabla_{u_m}\widehat{\mathrm{NMD}}$**.
Carrying it through,

$$\nabla_{u_m}\widehat{\mathrm{NMD}} \approx \frac{2}{B(B-1)}\,c\,(B-1)\,\hat u_m = \frac{2c}{B}\hat u_m,$$

so $u_m v^\top / N = (t\hat u_m)\big(\tfrac{2c}{B}\hat u_m^\top\big)\big/\big(\tfrac{2c}{B}t\big) = \hat u_m \hat u_m^\top$
and $P_{u_m} \to I - \hat u_m \hat u_m^\top$ — which *is* the orthogonal projector the
corollary claims, and which is consistent with Euler's identity (6) in the limit. **So
the stated conclusion is correct and the intermediate display is wrong.** This is a
presentation error, not a substantive one, and the corollary's qualitative content
(vanishing deviation ⇒ $P \to I$, unprojected gradient, escape from a degenerate niche;
dominant deviation ⇒ contraction along $u_m$, suppressing runaway heterogeneity)
stands. It is recorded here because a reader deriving from the printed line would get a
non-projector. *(This is my derivation, not the paper's; worth a `math-reviewer` pass
before it is repeated in a citing document.)*

*(iii) The Gaussian assumption does not hold in the implemented system.* Lemma 6
requires an unsquashed Gaussian with linear mean, but the continuous-control policies
apply $\tanh$. App. B.5 addresses this honestly and is worth reading in full: the
push-forward of a Gaussian under $\tanh$ is non-Gaussian, $W_2$ between two such
distributions has no closed form and must be computed numerically, and the exact
identity degrades to a Lipschitz **inequality**

$$W_2(\pi_m \circ \tanh^{-1}, \pi_n \circ \tanh^{-1}) \le L_{\tanh}\, W_2(\pi_m, \pi_n) = L_{\tanh}\lVert \mu_m - \mu_n\rVert_2, \qquad L_{\tanh} = 1,$$

so pre-activation NMD **upper-bounds** action-space NMD and preserves ordering but does
not equal it. Theorem 3's chain rule acquires a $\operatorname{diag}(\operatorname{sech}^2(z_m))$
Jacobian, with the projection structure preserved only "in the unsaturated regime …
with multiplicative error $O(\lVert z_m\rVert^2)$". The authors argue saturation acts as
a *complementary* gate rather than a violation, which is a reasonable reading. But the
abstract's "we prove that this construction ensures that diversity does not interfere
with reward maximization **by design**" should be read as holding exactly for the
idealised linear-Gaussian model and approximately for the system actually trained.

### 2.7 Discrepancies between the paper's prose and its own figures

Two, both in §5.2, both in the direction of over-claiming for baselines rather than for
the method — so they do not flatter the authors, but they do mean the prose cannot be
quoted as a source of values.

1. **"On Reverse Transport, all methods reach competitive completion rates except PS."**
   The figure shows CASH's median completion at ≈33 %, the same as PS, with a box
   spanning 33–100 % — i.e. CASH is bimodal across seeds and its median is *not*
   competitive. [digitized, Fig. 2a]
2. **"On Dispersion … CASH drops to roughly 50 %, DiCo to roughly 80 %, and HyperMARL
   and PS collapse."** The figure shows **CASH ≈33 %, HyperMARL ≈65.5 %, DiCo ≈85 %,
   PS ≈50.5 %** [digitized, Fig. 2c]. The prose appears to have swapped CASH and PS,
   and nothing on this panel "collapses" — the lowest median is CASH at a third. The
   genuine collapse is on **Football**, where all four baselines are at 0.

Neither error changes the paper's conclusions. Both mean that **the four-benchmark
comparison must be cited from the digitized figure, not from §5.2's sentences.**

### 2.8 What this contributes to the report

- **It populates the low-rank rung.** Before this paper the corpus jumped from
  per-channel affine (FiLM) to whole-tensor generation (HyperMARL, Marquis, HyPoGen)
  with nothing in between. This is a rank-8 additive delta on one layer, with an
  explicit efficiency rationale, evaluated against both neighbours on the spectrum
  (HyperMARL above it, DiCo's per-agent deviation beside it).
- **It supplies the corpus's only capacity sweep** — and the sweep is flat. Any argument
  in the report of the form "FiLM is too low-capacity for this job" now has to contend
  with a paper in which 32× more adapter capacity buys nothing measurable.
- **It reopens the self-conditioning question** that HyperMARL appeared to settle, and
  supplies the variable — **query frequency** — that reconciles the two results without
  either being wrong. This should be carried into the report as an explicit second axis
  alongside "what the conditioner reads".
- **It documents a second independent instability attributed to per-timestep
  regeneration** (CASH), which is the closest thing the corpus has to evidence about a
  per-step modulator's stability. It is an attribution, not an experiment — flag it as
  such.
- **It names the experiment nobody has run**: one architecture, one conditioner,
  generator query frequency swept from per-episode → per-event → per-step. If the report
  wants a single recommendation for future work, this is a strong candidate. *(An
  implementation of this would need `senior-developer` to scope; nothing here is a code
  plan.)*

### Appendix: Section-by-Section Backbone

Preserving the paper's own order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Current MARL diversity frameworks "bind fixed behaviors to fixed agent identities". Missing ingredient: **events** — state changes that induce qualitative task changes. Two components: **NMD**, a distance metric that stays well-defined when behaviours are transient and agent-agnostic; and an **event-based hypernetwork generating LoRA modules over a shared team policy**. Claims a proof that diversity does not interfere with reward maximisation by design, plus zero-shot generalisation and being "the only method that solves tasks requiring sequential behavior reassignment". |
| 1 | **Introduction** | Cooperation "hinges less on agent identity than on agent behavior at any given moment". Motivating examples: a quadrotor losing power, a defender reacting to a possession change. Rejects the shared assumption behind per-agent heterogeneous components, agent-specific generated weights, and partitioned action spaces — namely that behaviours are tied to agents. Three requirements ⇒ three contributions: a behaviour-centric metric, an event-driven LoRA hypernetwork, and a diversity-constrained objective with a gradient-alignment proof. **Footer: "Preprint."; margin: arXiv:2605.12388v2, 13 May 2026.** |
| 2 | **Related work** | Three axes. *Temporal assignment*: existing methods either fix one behaviour per agent per episode (HyperMARL, DiCo, …) or adapt on a fixed schedule regardless of context (CASH, …); this paper advocates a third, event-based category. *Behaviour representations*: explicit per-behaviour policies, conditioning a shared policy on identity/capability, or learning a latent behaviour space — all condition on something other than task events. *Quantifying diversity*: auxiliary rewards/losses (no guarantee) versus hard constraints (guarantee, but need an a-priori target); NMD is positioned as an SND successor that survives dynamic allocation. |
| 3 | **Background** | POMG tuple augmented with $B$, the behaviour manifold, defined as a property of the task. Capability descriptors are folded **into the observation**, so diversity means different actions from identical inputs. **Events as triggers**: augment with discrete $\Xi$ and detector $E : S \to \Xi\cup\{\varnothing\}$; an event induces a non-stationary transition that displaces the system onto a new optimal trajectory manifold. Event sources used: own-observation change (LiDAR), team-composition change (agent added/removed), environment signal (door opens). Problem formulation: learn $B$ and an event-conditioned map $f : O\times\Xi \to B$ that generalises zero-shot across agent count, capabilities, and event sequences. |
| 4 | **Framework** | Three-part roadmap: metric, architecture, diversity control. |
| 4.1 | NMD | Def. 1 (double integral over $B\times B$ of expected $W_2$); Prop. 2 (pseudometric, metric under separation); the empirical estimator, unbiased under i.i.d. sampled behaviours, instantiated over a **parallel batch of environments**. Explicit contrast with SND: no agent indices. |
| 4.2 | **Architectural realization** | Three requirements: (i) behaviour as a function of local observation and most recent event; (ii) cheap enough to avoid prohibitive per-timestep computation; (iii) room for diversity-preserving mechanisms. Transformer hypernetwork $g_\theta$ ingesting per-agent observation tokens + event encoding + `NMD_des`; emits $(C_m, D_m)$; **queried only on events, held fixed between them** — explicitly to avoid both "the static brittleness of episode-initial generation [HyperMARL]" and "the cost and instability of per-step regeneration [CASH]". Eq. (3): shared backbone plus $\alpha D_m C_m \phi$. Three design notes: low rank stabilises optimisation and shrinks output; **final-layer placement makes the deviation enter linearly**, which is what makes diversity maintenance and gradient projection tractable; the shared backbone carries task-general structure. |
| 4.3 | **Diversity control** | Eq. (4): $\alpha = \mathrm{NMD}_{\text{des}} / \widehat{\mathrm{NMD}}(\{u_m\})$, so realised diversity equals the target exactly by linearity. Generalises DiCo from fixed agent indices to a time-varying behaviour set. **Theorem 3**: $\nabla_{u_m}R = \alpha P_{u_m}(\nabla_{z_m}R)^\top$ with $P_{u_m}$ idempotent — diversity enters as a projector on the reward gradient, not as a regulariser. **Corollary 4**: vanishing deviation ⇒ $P \to I$ (escape a degenerate niche); dominant deviation ⇒ contraction along $u_m$ (suppress runaway heterogeneity). |
| 5 | **Experiments** | Four questions: Q1 competitiveness, Q2 zero-shot generalisation, Q3 sequential event-driven allocation, Q4 unseen event sequences. |
| 5.1 | Setup | Baselines HyperMARL / CASH / DiCo (SND grid-searched per task, best reported) / PS. Six VMAS environments. Events used: agent removal, capability modification, target-diversity change, environment change (door), LiDAR reading change. |
| 5.2 | **Q1** | Fig. 2, completion rate / average reward / episode length, 5 seeds. "Systematically ranks top-1, achieving a completion rate of at least 95 % across all tasks and significantly outperforming all baselines on the more complex Football task." Reverse Transport separates on **episode length** rather than completion — the method terminates earliest, indicating "more direct trajectories rather than merely succeeding more often". **Two sentences in this subsection misdescribe the figure — see §2.7.** |
| 5.3 | **Q2** | Three generalisation axes. HyperMARL excluded from the agent-count axis because its architecture cannot accommodate team-size changes; DiCo and PS policies replicated. Capability axis run as independent training runs per capability value, with capabilities concatenated to observations for this method and CASH. Diversity-target axis needs no retraining. Claimed stable across all three including out-of-distribution; NMD stable over ~two orders of magnitude, with a task-dependent "good" region. Presented as the empirical counterpart of Theorem 3. |
| 5.4 | **Q3** | Pressure Plate. Only method that completes the task. **Ablation without event re-querying fails** — agents statically assigned, "the final agent remaining stuck behind the door". Notes that sequential strategies emerge **without explicit time awareness**, an emergent property of decoupling identity from behaviour. t-SNE of $B$ over 128 replications shows distinct behavioural clusters. |
| 5.5 | **Q4** | Unseen event sequences: random agent removal in Football, targeted removal in Pressure Plate, mid-episode diversity change in Wind Flocking. Table 4c numbers. Wind Flocking qualitatively tracks `NMD_des`: inter-agent distance grows monotonically with NMD between steps 20 and 120 and contracts at step 170 — "confirms that `NMD_des` acts as a direct, interpretable control … rather than as a soft regularization target". |
| 6 | **Conclusion, limitations, future work** | Restates the event-driven thesis and the identity/behaviour decoupling. Highlights that sequential assignment emerges "despite the absence of a memory mechanism (e.g., RNN)". **Three limitations**: expressivity bounded by the LoRA representation (partly probed by the rank ablation); **events are defined a priori by domain knowledge** — inferring them end-to-end or by latent discovery is future work, as is automating the choice of `NMD_des`; and the hypernetwork is **centralised**, needing all agents' observations. |
| A | Extended related work | Longer treatment of behaviour typing, latent role spaces, action-space partitioning, and the auxiliary-loss-versus-constraint split. |
| B | **Proofs** | B.1 assumptions A1–A5 — note **(A3) Gaussian policy with shared, observation-independent $\Sigma$** and **(A4) linear LoRA parameterisation with deterministic $u_m$**. B.2 Prop. 2. B.3 Lemma 6 (Olkin–Pukelsheim, trace term vanishes) and Theorem 3 via Euler's homogeneous function theorem. B.4 Corollary 4 limits. **B.5 the honesty section**: bounded action spaces and $\tanh$ squashing break Lemma 6's closed form; the identity degrades to a Lipschitz upper bound with $L_{\tanh} = 1$; Theorem 3 acquires a $\operatorname{sech}^2$ Jacobian and holds with $O(\lVert z_m\rVert^2)$ error in the unsaturated regime; saturation is argued to be a complementary gate rather than a violation. |
| C | Experimental details | Prose descriptions of all six tasks. ~1000 total compute hours on one RTX 2080 Ti + Xeon Gold 6248R. |
| D.1 | Average episode rewards | Fig. 6 learning curves, 5 seeds, six tasks. **Models evaluated at best-performing checkpoints, not final.** CASH is singled out as "shaky", failing to converge in some independent runs, attributed to per-timestep hypernetwork re-querying making the policy "highly sensitive to minor fluctuations in the hypernetwork's output". |
| D.2 | **LoRA rank ablation** | Navigation, 5 seeds, $r \in \{2,4,8,16,32,64\}$. $r=8$ selected as the "sweet spot". **The figure shows no separation between any of the six ranks.** Repeats the assertion that $r \ll d$ "significantly stabilizes optimization relative to generating full dense matrices" — with no dense control run. |
| E | Broader societal impact | Search-and-rescue and inspection framing; dual-use acknowledgement; a note that treating behaviour as a task property gives "a more democratic model of cooperation, in which roles emerge from circumstance rather than from identity". |
| Table 1 | Hyperparameters | $10^7$ steps ($1.5\times10^8$ Football), 128 parallel envs, 8 minibatches, MAPPO defaults. **Method**: backbone `[128,128]`, critic `[128,128]`, LR $6\times10^{-4}$, **2 transformer blocks, 2 heads, embedding 64, MLP hidden 256, LoRA rank 8**. **DiCo**: `[128,128]` homogeneous + `[128,128]` per-agent, LR $10^{-4}$, SND grid $\{0.1,0.2,0.5,0.9,1.0,1.1,1.5,2.0\}$ with best = 1.0 (Navigation, Dispersion), 0.1 (Reverse Transport), 0.2 (Football). **HyperMARL baseline**: hypernetwork width 64, agent nets `[64,64]`, LR $5\times10^{-4}$, embedding dim 8. **CASH**: `[128,128]` policy and critic, GRU 128, LR $2\times10^{-3}$, hypernetwork hidden 64 × 4 layers, two-layer decoder. |

---

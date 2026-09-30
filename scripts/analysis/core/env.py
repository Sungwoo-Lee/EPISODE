#!/usr/bin/env python3
"""env.py - everything derived from a run's own saved config, in one place.

These five helpers existed in three copies each across the analysis layer, and every copy had
drifted textually. Before consolidating them they were tested for BEHAVIOURAL equivalence on real
configs, because textual drift and behavioural drift are different questions and only the second one
decides whether merging is safe:

    smell_channels        3 copies, 3 distinct texts, ONE distinct result   -> merged as-is
    nociception_kernel    2 copies, 2 distinct texts, ONE distinct result   -> merged as-is
    listcol               3 copies, 3 distinct texts, ONE distinct result   -> merged as-is
    slot_layout           3 copies, 3 distinct texts, THREE distinct results
    smell_channels        -> wrapper over `scent_spec` (2026-10-01, hypervigilance tooling)

`slot_layout` genuinely differed, and the difference is worth stating precisely because it is the
kind that looks alarming and is not: all three agree on every slot list any caller reads - `pred`,
`neutral`, `bush`, `rock`, `food`, `ambush` are identical - and differ only in whether they also
return the convenience counts `n_animal`, `n_obs`, `n_res`. This module returns the superset. That is
safe only because no caller iterates the dict or takes its length; every one of the four callers
subscripts it by name, which was checked rather than assumed.

The configs these read are the ones the TRAINER saved beside each run's checkpoints, not the ones in
the repo - so the layout always describes the world the agent was actually in.
"""
from __future__ import annotations
from dataclasses import dataclass

import numpy as np


def _alloc(d: dict, family: str) -> int:
    """How many slots this declaration allocates.

    `count_high` is the ALLOCATION size, not the sampled count: the store's columns are allocated
    for the maximum and unused slots are masked by `*_active`. A declaration with a FIXED `count`
    allocates exactly that many, so the two spellings are alternatives rather than one being a
    default for the other -- which is why neither is filled in silently when both are absent.
    The maintained basic levels use both: 00-02 and the `tree` on 05/06 declare `count`, while
    03/04 declare `count_low`/`count_high`. Reading only `count_high` raised KeyError on five of
    the seven, which is how this was found.
    """
    if "count_high" in d:
        return int(d["count_high"])
    if "count" in d:
        return int(d["count"])
    raise KeyError(
        f"{family} declaration {d.get('name', d.get('class', d.get('type', '?')))!r} has neither "
        f"'count_high' nor 'count'; slot allocation cannot be derived from it")


def slot_layout(cfg: dict) -> dict:
    """Entity / obstacle / resource slot indices, derived from the run's own config.

    Slots are laid out by declaration order within each family, so the index of an animal in the
    step table's `animal_row` column is its position here. `count_high` rather than the sampled
    count: the columns are allocated for the maximum, and unused slots are masked by `animal_active`.
    """
    env = cfg["environment"]
    pred, neu, s = [], [], 0
    for e in env["entities"]:
        n = _alloc(e, "entity")
        (pred if e["class"] == "predator" else neu).extend(range(s, s + n)); s += n
    bush, rock, s = [], [], 0
    for o in env["obstacles"]:
        n = _alloc(o, "obstacle")
        (bush if o.get("hides_agent") else rock).extend(range(s, s + n)); s += n
    food, amb, s = [], [], 0
    for r in env["resources"]:
        n = _alloc(r, "resource")
        (amb if max(r.get("damage", [0, 0])) > 0 else food).extend(range(s, s + n)); s += n
    return dict(pred=pred, neutral=neu, bush=bush, rock=rock, food=food, ambush=amb,
                n_animal=len(pred) + len(neu), n_obs=len(bush) + len(rock),
                n_res=len(food) + len(amb))


LAYOUTS = ("difference", "single", "sum")


@dataclass(frozen=True)
class ScentSpec:
    """How predator-like one animal smells, for the odour layout this run was trained in.

    Three layouts are accepted and nothing else (hypervigilance tooling plan, A2):

        difference  two emitting channels, predators higher on one and rabbits on the other
                    (every world before 2026-10); statistic = x_a - x_b
        single      one emitting channel, predators higher; statistic = x_a
        sum         two or more emitting channels on which each class has the SAME mean, predators
                    higher on all of them (the ratio carries no identity); statistic = sum of them

    For Gaussian recipes of equal spread the log-likelihood ratio "predator vs rabbit" is linear in
    the statistic: LLR(s) = llr_scale * (s - midpoint). Both numbers are derived from the saved
    config (class means and spreads), never typed. Clipping to [0, 1] is ignored, as in the study.
    """
    layout: str
    channels: tuple
    midpoint: float
    llr_scale: float
    pred_mean: tuple
    rab_mean: tuple
    sd: tuple

    def statistic(self, prop):
        """prop[..., n_channels] -> the layout's statistic (same expression as before for 'difference')."""
        if self.layout == "difference":
            a, b = self.channels
            return prop[..., a] - prop[..., b]
        if self.layout == "single":
            return prop[..., self.channels[0]]
        out = prop[..., self.channels[0]]
        for c in self.channels[1:]:
            out = out + prop[..., c]
        return out

    def intensity(self, prop):
        """Total animal odour on the emitting channels (same expression as before for 'difference')."""
        if self.layout == "difference":
            a, b = self.channels
            return prop[..., a] + prop[..., b]
        return self.statistic(prop)

    def llr(self, s):
        return self.llr_scale * (np.asarray(s, dtype=np.float64) - self.midpoint)

    @property
    def statistic_equals_intensity(self) -> bool:
        return self.layout != "difference"

    def channel_scale(self, c: int) -> tuple:
        """(midpoint, nats per unit) for ONE channel read alone, from the config's means and SD.

        The S1 matched control reading (plan A6) reads the control's channel 1 on its own evidence
        scale: means 0.7 / 0.5, SD 0.3 -> midpoint 0.6, 0.2 / 0.09 nats per unit.
        """
        mp, mr, sd = self.pred_mean[c], self.rab_mean[c], self.sd[c]
        var = sd * sd
        return (0.5 * (mp + mr), (mp - mr) / var if var > 0 else float("nan"))

    def as_dict(self) -> dict:
        return {"layout": self.layout, "channels": list(self.channels), "midpoint": self.midpoint,
                "llr_scale": self.llr_scale, "pred_mean": list(self.pred_mean),
                "rab_mean": list(self.rab_mean), "sd": list(self.sd),
                "statistic_equals_intensity": self.statistic_equals_intensity}


def _class_mean(ent, key, predator: bool):
    rows = []
    for e in ent:
        if (e["class"] == "predator") != predator:
            continue
        if key not in e:
            raise SystemExit(f"animal declaration {e.get('tag', e.get('class'))!r} has no "
                             f"{key!r}; the scent evidence scale cannot be derived without it")
        rows.append(e[key])
    if not rows:
        raise SystemExit(f"this run declares no {'predator' if predator else 'non-predator'} "
                         f"animal; predator-likeness of a scent is undefined here")
    return np.asarray(np.mean(rows, axis=0), dtype=np.float64)


def scent_spec(cfg: dict) -> ScentSpec:
    """Infer the odour layout of this run from its saved config, and refuse anything unrecognised."""
    ent = cfg["environment"]["entities"]
    pm = _class_mean(ent, "properties", True)
    nm = _class_mean(ent, "properties", False)
    d = pm - nm
    E = [int(c) for c in np.flatnonzero((pm != 0) | (nm != 0))]
    dE = d[E] if E else np.array([])
    why = (f"predator mean {pm.tolist()}, rabbit mean {nm.tolist()}; accepted layouts are "
           f"'difference' (two channels, opposite signs), 'single' (one channel, predators "
           f"higher) and 'sum' (equal-mix channels, predators higher on all)")
    if len(E) == 2 and (dE > 0).sum() == 1 and (dE < 0).sum() == 1:
        layout, chans = "difference", (int(np.argmax(d)), int(np.argmin(d)))
        w = np.zeros_like(d); w[chans[0]], w[chans[1]] = 1.0, -1.0
    elif len(E) == 1 and dE[0] > 0:
        layout, chans = "single", (E[0],)
        w = np.zeros_like(d); w[E[0]] = 1.0
    elif (len(E) >= 2 and (dE > 0).all() and np.allclose(pm[E], pm[E][0], rtol=0, atol=1e-9)
          and np.allclose(nm[E], nm[E][0], rtol=0, atol=1e-9)):
        layout, chans = "sum", tuple(E)
        w = np.zeros_like(d); w[E] = 1.0
    else:
        raise SystemExit(f"this run's odour config fits no accepted scent layout: {why}")
    ps = _class_mean(ent, "properties_std", True)
    ns = _class_mean(ent, "properties_std", False)
    if not np.allclose(ps[E], ns[E], rtol=0, atol=1e-12):
        raise SystemExit(f"predator and rabbit odour spreads differ on the emitting channels "
                         f"({ps[E].tolist()} vs {ns[E].tolist()}); the equal-spread evidence scale "
                         f"does not apply")
    mu_p, mu_r = float(w @ pm), float(w @ nm)
    var = float(np.sum(w * w * ps * ps))
    k = (mu_p - mu_r) / var if var > 0 else float("nan")
    return ScentSpec(layout=layout, channels=chans, midpoint=0.5 * (mu_p + mu_r), llr_scale=k,
                     pred_mean=tuple(pm.tolist()), rab_mean=tuple(nm.tolist()),
                     sd=tuple(ps.tolist()))


def smell_channels(cfg: dict) -> tuple[int, int]:
    """The two olfactory channels that separate predators from neutrals, derived not assumed.

    Kept for the two-channel callers (collect_hiding_drivers.py and older scripts); a wrapper over
    `scent_spec`, so there is one inference of the odour layout, not two.
    """
    spec = scent_spec(cfg)
    if spec.layout != "difference":
        raise SystemExit(f"this run's odour layout is '{spec.layout}'; smell_channels() is defined "
                         f"only for the two-channel difference layout -- use scent_spec()")
    return spec.channels


def nociception_kernel(cfg: dict) -> np.ndarray:
    """The alpha kernel the environment convolves the injury buffer with (config_loader.py:1424)."""
    n = int(cfg["sensory"]["interoceptive_kernel_length"])
    tau = float(cfg["sensory"]["interoceptive_kernel_tau"])
    k = np.arange(n, dtype=np.float64)
    raw = (k / tau) * np.exp(1.0 - k / tau)
    return raw / raw.sum()


def perceived_nociception(inj, t, estart, kernel):
    """Rebuild the scalar the nociceptor actually hands the agent, row by row.

    Mirrors core.py:115 (roll the buffer, write the new injury at slot 0) and core.py:1112 (the
    buffer is ZEROED at reset, so the reset row's injury is never in it). The `src > estart` guard
    is strict for exactly that reason - including the reset row was a real bug once (Known Bugs,
    2026-08-25) and it leaks the randomised starting injury into the first steps as if the agent had
    felt it immediately, which is precisely the claim the sensor-ladder study tests.
    """
    idx = np.arange(len(t))
    out = np.zeros(len(t))
    for j in range(1, len(kernel)):
        src = idx - j
        ok = src > estart
        out[ok] += kernel[j] * inj[src[ok]]
    return out


def listcol(col, width):
    """Fixed-width parquet list column -> (n, width) array without the slow to_pylist path."""
    ch = col.chunks if hasattr(col, "chunks") else [col]
    return np.concatenate([c.flatten().to_numpy(zero_copy_only=False)
                           for c in ch]).reshape(-1, width)

"""Readers for the aggregated real-agent death data (figures a1-a5). Never touches the trajectory stores.

predator_deaths.json and by_predator_count.json were written on 2026-10-11 by predator_deaths.py and
by_predator_count.py (this folder) over 27 stores of 1,000,000 evaluation episodes each. The Wave-2 stores
(basicq2_w2) cover levels 02-06 with an ordinary agent (t1none) and a modulated agent (t16quad; level 02 has
the ordinary agent only). Their "level 06" was collected on 2026-09-22, BEFORE the 2026-09-30 renumbering:
that world is today's level 07 (sensory noise), and it is labelled so everywhere.
"""
import json, os

import _common as C

DATA = os.path.join(C.FIG, "data")
STATES = ("bush", "out_ate20", "out_toward", "out_other")
ACT_LABEL = {"out_ate20": "just ate (ate in the last 20 steps)", "out_toward": "heading to food",
             "out_other": "roaming (anything else outside a bush)"}
LEVEL_LABEL = {"02": "level 02", "03": "level 03", "04": "level 04", "05": "level 05",
               "06": "old level 06 = today's level 07"}
AGENT = {"t1none": "ordinary", "t16quad": "modulated"}
L05_STORES = ["basicq2_w2/rppo_bq2cover_lvl05_t1none_s42", "basicq2_w2/rppo_bq2cover_lvl05_t16quad_s42",
              "hvsmell/rppo_l05body_w0000_t1none_s42", "hvsmell/rppo_l05body_w0000_t16quad_s42"]


def deaths():
    return json.load(open(os.path.join(DATA, "predator_deaths.json")))


def counts():
    return json.load(open(os.path.join(DATA, "by_predator_count.json")))


def wave2():
    """[(store, level '02'..'06', agent)] for the Wave-2 stores, in level order."""
    out = []
    for s in deaths():
        if s.startswith("basicq2_w2/"):
            lv = s.split("lvl")[1][:2]; ag = s.split("_")[-2]
            out.append((s, lv, AGENT[ag]))
    return sorted(out, key=lambda x: (x[1], x[2] != "ordinary"))


def by_level():
    lv = {}
    for s, l, _ in wave2():
        lv.setdefault(l, []).append(s)
    return lv

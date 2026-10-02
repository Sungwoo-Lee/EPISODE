"""Shared paths and helpers for the 'Continual Worlds' PLANNING page (docs/experiments/active/
continual_worlds/CONTINUAL_WORLDS.md). Figures 1-4 are design figures, drawn from the design's configs
(the concept worlds under configs/environment/experiment/continual_worlds/ and the schedules under
configs/continual/continual_worlds/) and from the design doc itself. The pilot-results figure (p5) is the
one results figure: it reads results/analysis/continual_worlds/pilot_readout.json (kind "training").

Same house pattern as scripts/analysis/studies/level05_body_interactions/page/_common.py (record_kind,
record_samples, save with the text guards and the phone-floor check). This folder sits FOUR levels
below the repo root, so ROOT walks five '..'.

Colour: on this project's pages blue / orange / green mean rest-in-cover / warm-up / eat, so these
figures use ink and greys, plus ONE accent (house.RED) where a figure needs a single highlight.
"""
import dataclasses, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house                                                          # noqa: E402
from figguards import (assert_min_text_px, assert_no_text_overlap,   # noqa: E402,F401
                       assert_ticks_dont_collide, COLUMN_PX)

DOC = os.path.join(ROOT, "docs/experiments/active/continual_worlds/CONTINUAL_WORLDS.md")
FIG = os.path.join(ROOT, "docs/experiments/active/continual_worlds/figures")
WORLD_DIR = os.path.join(ROOT, "configs/environment/experiment/continual_worlds")
SCHED_DIR = os.path.join(ROOT, "configs/continual/continual_worlds")
READOUT = os.path.join(ROOT, "results/analysis/continual_worlds/pilot_readout.json")
INVENTORY = os.path.join(ROOT, "docs/experiments/active/internal_state_interactions/BALANCE_SETTINGS_INVENTORY.md")

KIND = {"design": "design — settings and plan, no results yet",
        # same wording family as the level-05 page's "training" kind
        "training": "training logs — pilot runs, last 200,000 episodes, one seed"}

# The eight concepts, in the order the design doc's concept table uses (section 3.2). The file for each
# is found by its stem prefix, so the grid size in the file name is never typed here.
CONCEPTS = ["Nursery", "Home", "Forage", "Danger", "Famine", "Winter", "Fog", "Harsh"]
REFERENCE = "Home"

GREY = "#8a8f99"
ACCENT = house.RED
SMALLEST_PT = 9.5         # every hand-set text size in these figures; the ticks are 11 pt
FLOOR_PX = 685            # the page's .figscroll min-width; see save()

# EnvParams fields that describe the BODY (the stationary side). Grouped as the page groups them.
# Every one must be identical in all eight worlds (asserted by body_fields_identical()).
BODY_FIELDS = {
    "food energy": ["max_satiation", "max_nutrition", "food_nutrition_gain", "setpoint", "start_satiation",
                    "start_nutrition", "start_nutrition_low", "start_nutrition_high", "metabolic_cost",
                    "nutrition_to_satiation_scaling_factor", "overeating_death", "with_satiation",
                    "with_nutrition", "random_start_satiation", "random_start_nutrition",
                    "eating_nutrition_cost", "eating_reward_penalty", "eat_action_enabled",
                    "healing_nutrition_cost", "healing_nutrition_shortfall", "healing_nutrition_dependence",
                    "healing_hunger_low", "healing_hunger_high", "healing_hunger_floor",
                    "healing_overfull_floor", "healing_overfull_start"],
    "injury": ["max_injury", "start_injury_low", "start_injury_high", "recovery_base_rate",
               "recovery_accel_rate", "recovery_in_bush_multiplier", "smoothing_duration", "with_injury",
               "random_start_injury", "rest_action_enabled"],
    "body temperature": ["thermal_k_exchange", "thermal_k_loss", "thermal_k_metabolic",
                         "thermal_warming_rate_scale", "thermal_cooling_rate_scale", "temperature_setpoint",
                         "min_temperature", "max_temperature", "thermal_metabolic_coupling",
                         "thermal_metabolic_coupling_rate", "thermal_random_start_body_temp",
                         "thermal_start_body_temp_low", "thermal_start_body_temp_high",
                         "thermal_healing_cold_sensitivity", "thermal_healing_warm_sensitivity",
                         "thermal_injury_heat_exchange_gain", "thermal_injury_heat_exchange_mode"],
    "interoception": ["injury_observable", "nutrition_observable", "interoceptive_nociception_enabled",
                      "interoceptive_convolution_enabled", "interoceptive_kernel_length",
                      "interoceptive_kernel", "thermal_body_temp_observable"],
    "reward": ["death_penalty", "use_homeostatic_reward", "max_steps"],
}


def world_file(concept):
    hits = sorted(f for f in os.listdir(WORLD_DIR) if f.startswith(concept.lower() + "_") and f.endswith(".yaml"))
    assert len(hits) == 1, f"expected one config for {concept} in {WORLD_DIR}, found {hits}"
    return os.path.join(WORLD_DIR, hits[0])


def load_params():
    """{concept: EnvParams}, through the trainer's own loader (load_env_config -> load_env_params)."""
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    from src.environment.config_loader import load_env_config, load_env_params
    return {c: load_env_params(load_env_config(world_file(c))) for c in CONCEPTS}


def same(a, b):
    import numpy as np
    try:
        return bool(np.array_equal(np.asarray(a), np.asarray(b)))
    except Exception:
        return a == b


def body_fields_identical(P):
    """Fail loudly unless every body field is identical in every world. Returns the number of fields."""
    names = {f.name for f in dataclasses.fields(P[REFERENCE])}
    n = 0
    for grp, fields in BODY_FIELDS.items():
        for f in fields:
            assert f in names, f"EnvParams has no field {f!r} (group {grp}); update BODY_FIELDS"
            for c in CONCEPTS:
                if not same(getattr(P[c], f), getattr(P[REFERENCE], f)):
                    raise SystemExit(f"BODY RULE DIFFERS: {f} ({grp}) is {getattr(P[c], f)!r} in {c} but "
                                     f"{getattr(P[REFERENCE], f)!r} in {REFERENCE} -- the body is not stationary")
            n += 1
    return n


def doc_text():
    return open(DOC).read()


def record_samples(stem, rows):
    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(FIG, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            assert "|" not in r["what"] + r["note"], f"'|' is the field separator: {r}"
            pct = 100.0 * r["used"] / r["total"] if r["total"] else 0.0
            u = f"{r['used']:,}" if isinstance(r["used"], int) else r["used"]
            t = f"{r['total']:,}" if isinstance(r["total"], int) else r["total"]
            fh.write(f"{r['what']}|{u}|{t}|{pct:.1f}|{r['note']}\n")
    print(f"  wrote {stem}.data.txt ({len(rows)} rows)")


def record_kind(stem, kind):
    assert kind in KIND, kind
    os.makedirs(FIG, exist_ok=True)
    open(os.path.join(FIG, f"{stem}.kind.txt"), "w").write(kind + "\n")


def save(fig, stem, check_text=True):
    """Guards, then house.save, then the phone-floor check on the SAVED raster (see the level-05 page's
    _common.save: 9.5 pt at 220 dpi is 29.0 px, so the PNG must be at most 2209 px wide for 9 px text
    at the page's 685 px .figscroll floor)."""
    assert_no_text_overlap(fig)
    assert_min_text_px(fig)
    dpi = fig.dpi
    house.save(fig, os.path.join(FIG, stem), column_px=COLUMN_PX, check_text=check_text)
    from PIL import Image
    w = Image.open(os.path.join(FIG, f"{stem}.png")).size[0]
    need = w * 9.0 / (SMALLEST_PT * dpi / 72.0)
    if need > FLOOR_PX:
        raise SystemExit(f"{stem}: canvas {w}px needs a {need:.0f}px phone floor for 9px text, "
                         f"above the page's {FLOOR_PX}px; narrow the figure")
    print(f"  {stem}: canvas {w}px, phone floor needed {need:.0f}px (page gives {FLOOR_PX}px)")

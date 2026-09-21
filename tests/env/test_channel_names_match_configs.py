"""Every maintained config can actually record a video -- the standing guard.

WHAT THIS PROTECTS, IN PLAIN WORDS. Each sense's channel names now live in the
environment config, and the list has to be exactly as long as that sense's
channel count. Nothing checks that when the config LOADS -- a config whose names
disagree with its widths trains perfectly well and fails only when it tries to
write its first video, hours into a GPU run. This file moves that failure to
commit time: it resolves every maintained config and builds the recording's
display payload from it, failing by name on any file whose declaration does not
match what it actually resolves to.

WHY THE FAILURE CANNOT BE MOVED INTO THE LOADER INSTEAD. A new key read inside
`load_env_params` is read by the byte-parity gates too, and those load ~38
standalone configs RAW, with no `extends:` resolution -- 23 of them under
`archive/`, which the project's maintenance policy forbids migrating. Putting the
check there would trade a display bug for a red gate on configs nobody maintains.
So the check lives here, where it can use the resolving loader.

TWO RULES THAT LOOK FUSSY AND ARE NOT:

  * SKIP IS PERMITTED ONLY for files sitting DIRECTLY under `configs/continual/`.
    Those are curriculum SCHEDULES, not environment configs, and every one fails
    on an unrelated missing key. Everything else must resolve or this test fails
    naming the file. A blanket skip-on-load-error would let a NEW maintained
    world that fails to load slip through silently -- the floors below catch
    removals, not additions, which is why the rule is by LOCATION and not by
    outcome.

  * A `channel_display_from_config` raise is ALWAYS a failure, never a skip.
    That is the exact condition this file exists to detect.

THE ENABLED-SENSE RULE. A sense's keys are checked only when that sense resolves
ENABLED. The two olfaction-parity configs switch vision off, so they must PASS
with olfaction names alone; demanding vision names from them would fail a correct
file, and skipping them quietly would hide a real omission later.
"""
import glob
import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ.setdefault("JAX_PLATFORMS", "cpu")


def _collect():
    """The sweep roots, as a GLOB rather than a hand-written list.

    Copied from `test_backward_compat_configs._collect_all_configs` -- including
    its `archive/` exclusion, which quotes the maintenance policy -- but NOT its
    loader: that one builds a raw `Config` with no `extends:` resolution, which
    would resolve a fraction of these and skip every ladder world.
    """
    files = sorted(
        [p for p in glob.glob(str(_ROOT / "configs/environment/experiment/**/*.yaml"),
                              recursive=True)
         if os.sep + "archive" + os.sep not in p]
        + glob.glob(str(_ROOT / "configs/continual/**/*.yaml"), recursive=True)
        + glob.glob(str(_ROOT / "configs/verification/**/*.yaml"), recursive=True)
    )
    base = str(_ROOT / "configs/environment/default.yaml")
    if base not in files:
        files.append(base)
    return files


CONFIGS = _collect()
IDS = [os.path.relpath(p, _ROOT) for p in CONFIGS]


def _is_curriculum_schedule(path: str) -> bool:
    """A file sitting DIRECTLY under `configs/continual/` -- not in a subdirectory.

    `configs/continual/nmn_double_return_stages/*` ARE environment configs and
    must resolve; the schedules beside them are not.
    """
    return Path(path).parent == _ROOT / "configs" / "continual"


def test_the_sweep_actually_collects_the_configs_it_claims_to():
    """A floor, so an empty or broken glob cannot pass as a clean sweep."""
    assert len(CONFIGS) >= 32, (
        f"the sweep collected only {len(CONFIGS)} configs; it is supposed to "
        f"cover every maintained env config under configs/environment/, "
        f"configs/verification/ and configs/continual/")


@pytest.mark.parametrize("path", CONFIGS, ids=IDS)
def test_every_maintained_config_can_write_a_recording(path):
    """Resolve the config, then build the payload a recording would carry."""
    from src.environment.config_loader import load_env_config, load_env_params
    from src.utils.eval_recording import channel_display_from_config

    rel = os.path.relpath(path, _ROOT)
    try:
        cfg = load_env_config(path)
        params = load_env_params(cfg)
    except Exception as exc:
        if _is_curriculum_schedule(path):
            pytest.skip(f"{rel}: curriculum schedule, not an env config ({exc!r:.90})")
        raise AssertionError(
            f"{rel} does not resolve to EnvParams: {type(exc).__name__}: {exc}\n"
            f"Every file under configs/environment/**, configs/verification/** and "
            f"configs/continual/nmn_double_return_stages/ must resolve. Only the "
            f"curriculum schedules directly under configs/continual/ may skip."
        ) from exc

    # A raise here is ALWAYS a failure -- it is the condition under test.
    payload = channel_display_from_config(cfg, params)

    for sense, enabled, width, names_key, groups_key in (
        ("Olfaction", bool(params.olfactory_enabled),
         int(params.olfactory_vector_size),
         "sensory.olfactory_channel_names", "sensory.olfactory_channel_groups"),
        ("Visual", bool(params.visual_sensor_enabled),
         int(params.visual_vector_size),
         "sensory.visual_channel_names", "sensory.visual_channel_groups"),
    ):
        if not enabled:
            assert sense not in payload, (
                f"{rel}: {sense} is disabled but the payload carries an entry for it")
            continue
        assert sense in payload, (
            f"{rel}: {sense} resolves ENABLED but the recording payload has no "
            f"entry for it. Declare {names_key} and {groups_key} in this file.")
        got = len(payload[sense]["names"])
        assert got == width, (
            f"{rel}: {names_key} has {got} entries but this config resolves to "
            f"{width} {sense} channels. A child config replaces a list wholesale "
            f"or not at all -- it cannot shorten an inherited one, so a file that "
            f"sets its own width must declare that sense's names in the SAME file.")
        for group in payload[sense]["groups"]:
            for ch in group["channels"]:
                assert 0 <= ch < width, (
                    f"{rel}: {groups_key} group {group['name']!r} names channel "
                    f"{ch}, but this config has only {width} {sense} channels")


def test_enough_configs_actually_resolve_to_be_a_real_sweep():
    """The second floor. Without it, a change that made everything unresolvable
    would leave this file green on a sweep that validated nothing."""
    from src.environment.config_loader import load_env_config, load_env_params

    resolved = 0
    for path in CONFIGS:
        try:
            load_env_params(load_env_config(path))
            resolved += 1
        except Exception:
            pass
    assert resolved >= 19, (
        f"only {resolved} of {len(CONFIGS)} collected configs resolve to "
        f"EnvParams; the sweep is supposed to validate at least 19")


def test_the_two_olfaction_parity_configs_pass_with_olfaction_names_alone():
    """The enabled-sense rule, stated as its own case so it cannot regress into
    "vision names required everywhere"."""
    from src.environment.config_loader import load_env_config, load_env_params
    from src.utils.eval_recording import channel_display_from_config

    for name in ("olfaction_parity_neutral", "olfaction_parity_predator"):
        path = _ROOT / f"configs/verification/{name}.yaml"
        assert path.exists(), f"{path} is missing; this case must fail, never skip"
        cfg = load_env_config(str(path))
        params = load_env_params(cfg)
        assert bool(params.visual_sensor_enabled) is False
        payload = channel_display_from_config(cfg, params)
        assert set(payload) == {"Olfaction"}
        assert len(payload["Olfaction"]["names"]) == int(params.olfactory_vector_size)

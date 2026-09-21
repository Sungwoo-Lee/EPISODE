"""Channel names are DATA from the config, and a sense panel is a FIXED size.

WHAT THIS FILE IS FOR, IN PLAIN WORDS. The episode video draws one small map per
sensor channel and prints that channel's name under it ("Food", "Predator",
"Terrain"). Those names used to be a hardcoded table inside the renderer. They
now travel with the recording, put there from the environment config when the
recording is written. This file pins the three properties that change buys:

  1. A NAME CAN NEVER DISAGREE WITH THE CHANNEL IT LABELS. The names list is
     validated against the run's real channel count when the recording is
     written, and a mismatch raises naming BOTH numbers. There is no fallback
     default anywhere: a config that does not declare names cannot record.

  2. A SENSE PANEL IS THE SAME WIDTH FOR EVERY RUN. Smell is sized for five map
     slots and vision for six, whatever the run's channel count, so a
     one-channel run draws one normal-sized map and leaves the rest of the panel
     BLANK. That blank space is intended -- it is what lets two runs' panels be
     compared side by side -- and it is asserted here so nobody later "fixes" it.

  3. A MERGED MAP READS THE CHANNELS ITS GROUP NAMES. Vision's three terrain
     channels are drawn as ONE map. Which channels merge is now config data, so
     the painter must read the declared indices rather than a literal slice.
     A group declaring [1,2,3] must colour itself from channels 1-3.

WHY PROPERTY 3 HAS A SOURCE-TEXT ASSERTION AND NOT ONLY A BEHAVIOURAL ONE. The
defect it guards against is a painter that validates correctly, places the map
correctly, and then colours it from the wrong channels with no error at all --
`row[:3]` is a literal slice, so `{Terrain, [1,2,3]}` would have drawn channels
0-2 silently. A unit test written from the same assumption that produced that bug
would assert the same wrong thing, so the structural check below reads the
painter's SOURCE and fails if any channel index is spelled as a constant in it.
The project already uses this pattern for the map gap
(`test_dashboard_band_span.py`).

THE LEGACY ASYMMETRY, STATED SO IT IS NOT "SIMPLIFIED" AWAY. A recording made
before this change carries no names. It gets positional ones ("Channel 0") and
NO groups -- so an old 8-channel recording draws 8 maps, not 6, because the
terrain merge is data it does not carry. Its panel is therefore sized to what it
actually draws, `max(slots, drawn)`, NOT to the fixed slot count. Using the fixed
count everywhere would overflow every recording already on disk. This is the one
deliberate asymmetry in the design.
"""
import os
import re
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ.setdefault("JAX_PLATFORMS", "cpu")

from src.environment.dashboard import labels as LB  # noqa: E402
from src.environment.dashboard import palette as PAL  # noqa: E402
from src.environment.dashboard import panels as P  # noqa: E402


# ---------------------------------------------------------------------------
# builders -- every display in this file is built IN MEMORY, from literals.
#
# No case here names a config file. Two regression gates in this package have
# now gone dark because a config they named was deleted and the test skipped
# instead of failing, so a subject that can vanish is not used at all.
# ---------------------------------------------------------------------------
def _names(n, prefix="Ch"):
    return [{"name": f"{prefix}{i}", "qualifier": ""} for i in range(n)]


def _payload(n, groups=(), prefix="Ch"):
    return {"names": _names(n, prefix), "groups": [dict(g) for g in groups]}


TERRAIN = {"name": "Terrain", "channels": [0, 1, 2]}

#: The 8-channel reference display: the standard vision layout, with the three
#: terrain channels merged. `PANEL_MAP_SLOTS` is anchored to THIS rather than to
#: `default.yaml`, which now ships ONE vision channel and draws one map -- the
#: "equals what the shipped config draws" formulation would fail by construction.
REFERENCE_V8 = _payload(8, groups=(TERRAIN,))


def _display(sense, n, payload, *, key_present=True):
    return LB.ChannelDisplay.from_meta(sense, n, payload, key_present=key_present)


def _configured(sense, n, groups=()):
    return _display(sense, n, _payload(n, groups))


def _legacy(sense, n):
    return _display(sense, n, None, key_present=False)


def _ctx(*, vis_channels=8, vis_range=2, olf_channels=5, olf_range=1,
         channel_display=None):
    """A context with both senses drawn as diamond maps."""
    cells_v = P._diamond_cells(vis_range)
    cells_o = P._diamond_cells(olf_range)
    return P.LayoutContext(
        world_w=10, world_h=10, local_view_size=5,
        breakdown={"Satiation": 1,
                   "Olfaction": cells_o * olf_channels,
                   "Visual": cells_v * vis_channels,
                   "Collision": 5, "Proprioception": 4},
        thermal=False, intero_noc_enabled=False,
        olfactory_range=olf_range, visual_range=vis_range,
        visual_vector_size=vis_channels, olfactory_channels=olf_channels,
        channel_display=channel_display,
    )


# ---------------------------------------------------------------------------
# 1. the names must match the channels
# ---------------------------------------------------------------------------
def test_a_names_list_shorter_than_the_channel_count_raises_naming_both_numbers():
    with pytest.raises(ValueError) as exc:
        _display("Visual", 8, _payload(5))
    msg = str(exc.value)
    assert "5" in msg and "8" in msg, (
        f"the error must name BOTH numbers -- how many names were declared and "
        f"how many channels the run has. Got: {msg}")


def test_a_names_list_longer_than_the_channel_count_raises_naming_both_numbers():
    with pytest.raises(ValueError) as exc:
        _display("Olfaction", 5, _payload(6))
    msg = str(exc.value)
    assert "6" in msg and "5" in msg


@pytest.mark.parametrize("bad", [
    {"name": "", "qualifier": ""},
    {"name": None, "qualifier": ""},
    {"name": 3, "qualifier": ""},
])
def test_an_empty_or_non_string_channel_name_raises(bad):
    payload = {"names": [bad] + _names(4)[1:] + _names(1), "groups": []}
    payload["names"] = [bad] + _names(4, "X")
    with pytest.raises(ValueError):
        _display("Olfaction", 5, payload)


# ---------------------------------------------------------------------------
# 2. group validation
# ---------------------------------------------------------------------------
def test_a_group_naming_a_channel_that_does_not_exist_raises():
    with pytest.raises(ValueError) as exc:
        _display("Visual", 8, _payload(8, [{"name": "T", "channels": [7, 8, 9]}]))
    assert "9" in str(exc.value) or "8" in str(exc.value)


def test_a_group_repeating_a_channel_raises():
    with pytest.raises(ValueError):
        _display("Visual", 8, _payload(8, [{"name": "T", "channels": [0, 1, 1]}]))


def test_one_channel_in_two_groups_raises():
    with pytest.raises(ValueError):
        _display("Visual", 8, _payload(8, [
            {"name": "A", "channels": [0, 1]},
            {"name": "B", "channels": [1, 2]},
        ]))


def test_a_non_contiguous_group_raises():
    with pytest.raises(ValueError):
        _display("Visual", 8, _payload(8, [{"name": "T", "channels": [0, 2, 3]}]))


def test_a_group_of_one_channel_raises():
    """A group of one is a plain channel wearing a group's name."""
    with pytest.raises(ValueError):
        _display("Visual", 8, _payload(8, [{"name": "T", "channels": [0]}]))


def test_a_group_longer_than_the_palette_can_colour_is_refused_naming_both_numbers():
    """D8 part 3. The merged map is drawn in flat per-channel colours, and the
    terrain palette has exactly three. A four-channel group has no fourth colour,
    so it is refused rather than silently reusing one."""
    arity = len(PAL.TERRAIN_FILL)
    with pytest.raises(ValueError) as exc:
        _display("Visual", 8, _payload(8, [{"name": "T", "channels": [0, 1, 2, 3]}]))
    msg = str(exc.value)
    assert str(arity) in msg and "4" in msg, (
        f"the refusal must name the group's length and the palette's arity. Got: {msg}")


# ---------------------------------------------------------------------------
# 3. D8 -- the merged map reads the channels its group NAMES
# ---------------------------------------------------------------------------
def test_the_map_plan_carries_the_groups_declared_channels_not_a_position():
    plan = LB.map_plan("Visual", _configured("Visual", 8, [TERRAIN]))
    merged = [m for m in plan if m[2] == "terrain"]
    assert len(merged) == 1
    assert tuple(merged[0][3]) == (0, 1, 2)


def test_a_shifted_group_reads_the_shifted_channels():
    """THE ONE THAT WOULD HAVE CAUGHT THE BUG. `{Terrain, [1,2,3]}` must produce a
    merged map reading channels 1-3. Asserted against the channels the plan
    RETURNS -- never against `row[:3]`-shaped reasoning, which is the assumption
    under test."""
    shifted = _configured("Visual", 8, [{"name": "Terrain", "channels": [1, 2, 3]}])
    plan = LB.map_plan("Visual", shifted)
    merged = [m for m in plan if m[2] == "terrain"][0]
    assert tuple(merged[3]) == (1, 2, 3), (
        "the merged map still reports channels 0-2; a group is DATA now, so the "
        "painter would colour a [1,2,3] group from the wrong channels")
    plain = [m for m in plan if m[2] == "seq"]
    assert [m[3] for m in plain] == [0, 4, 5, 6, 7]


def test_a_plain_channels_map_carries_its_own_index():
    plan = LB.map_plan("Olfaction", _configured("Olfaction", 5))
    assert [m[3] for m in plan] == [0, 1, 2, 3, 4]
    assert all(m[2] == "seq" for m in plan)


def test_no_channel_index_is_spelled_as_a_constant_in_the_painter():
    """The structural half of D8, following this package's own `MAP_GAP` precedent.

    `row[:3]` was a literal slice and `P.TERRAIN_FILL` a hardcoded 3-tuple, so a
    group declaring other channels validated, placed correctly, and coloured
    itself from channels 0-2 with no error. Prose cannot stop the NEXT literal
    index; this can.
    """
    from src.environment.dashboard import painters as PN

    src = Path(PN.__file__).read_text()
    hits = re.findall(r"\b(?:row|vec)\[[^\]]*\d[^\]]*\]", src)
    assert hits == [], (
        f"painters.py subscripts a channel vector with a literal index: {hits}. "
        f"A channel index may never be a constant here -- the map plan carries "
        f"the group's declared channels, and the painter must read exactly those.")


# ---------------------------------------------------------------------------
# 4. the panel is a fixed size
# ---------------------------------------------------------------------------
def test_the_slot_constant_is_what_the_reference_display_actually_draws():
    """`PANEL_MAP_SLOTS` is anchored to an explicit 8-channel reference display,
    NOT to `default.yaml` -- the shipped base now runs ONE vision channel."""
    vis = _display("Visual", 8, REFERENCE_V8)
    assert len(LB.map_plan("Visual", vis)) == LB.PANEL_MAP_SLOTS["Visual"] == 6
    olf = _configured("Olfaction", 5)
    assert len(LB.map_plan("Olfaction", olf)) == LB.PANEL_MAP_SLOTS["Olfaction"] == 5


@pytest.mark.parametrize("n", [1, 8, 12])
def test_the_vision_panel_is_the_same_width_at_every_channel_count(n):
    """THE POINT OF THE WHOLE CHANGE. Panel width depends only on the sense."""
    groups = [TERRAIN] if n >= 3 else []
    ctx = _ctx(vis_channels=n, channel_display={"Visual": _payload(n, groups)})
    width = P._visual_min_size(ctx).w
    ref = _ctx(vis_channels=8, channel_display={"Visual": REFERENCE_V8})
    assert width == P._visual_min_size(ref).w


def test_a_configured_run_drawing_more_maps_than_there_are_slots_does_NOT_raise():
    """D4b, a USER DECISION taken on 2026-09-19: no channel ceiling. The extra
    maps are drawn past the panel edge and nothing refuses the config. The
    ABSENCE of a refusal is the decision, so it is asserted explicitly -- if this
    test ever fails, a limit crept back in."""
    over = _configured("Visual", 12, [TERRAIN])      # 1 + 9 = 10 maps into 6 slots
    assert len(LB.map_plan("Visual", over)) == 10
    assert LB.panel_map_slots("Visual", over) == 6   # must not raise


def test_an_over_slot_run_warns_naming_both_numbers(caplog):
    """Nothing is refused, but the silence goes. The warning names how many maps
    will be drawn and how many slots exist, so an accidental edit -- deleting the
    Terrain group takes vision from 6 maps to 8 -- is discoverable."""
    over = _configured("Visual", 8)                  # no group: 8 maps into 6 slots
    with caplog.at_level("WARNING"):
        assert LB.panel_map_slots("Visual", over) == 6
    text = caplog.text
    assert "8" in text and "6" in text, (
        f"the warning must name both numbers. Got: {text!r}")


def test_the_blank_space_at_one_channel_is_the_full_panel_minus_one_map():
    """A one-channel run draws ONE map and leaves five slots blank. The panel is
    six slots wide either way; what changes is how much of it is filled."""
    one = _configured("Visual", 1)
    assert len(LB.map_plan("Visual", one)) == 1
    assert LB.panel_map_slots("Visual", one) == 6


# ---------------------------------------------------------------------------
# 5. legacy recordings
# ---------------------------------------------------------------------------
def test_a_recording_with_no_names_gets_positional_names_and_no_groups():
    d = _legacy("Visual", 8)
    assert d.legacy is True
    assert d.names[0] == ("Channel 0", "")
    assert d.names[7] == ("Channel 7", "")
    assert d.groups == ()
    assert len(LB.map_plan("Visual", d)) == 8, (
        "a legacy recording carries no merge group, so it draws one map per "
        "channel -- 8, not 6")


def test_a_legacy_eight_channel_recording_is_sized_to_eight_not_six():
    """D5, and it is load-bearing. Sizing legacy to the fixed six would overflow
    EVERY recording already on disk, including all eleven render-audit cells."""
    assert LB.panel_map_slots("Visual", _legacy("Visual", 8)) == 8


def test_a_legacy_one_channel_recording_is_still_sized_to_the_full_panel():
    """`max(slots, drawn)` -- so a narrow legacy recording does not get a narrow
    panel either."""
    assert LB.panel_map_slots("Visual", _legacy("Visual", 1)) == 6


def test_legacy_is_keyed_on_the_top_level_key_not_on_a_missing_sense_entry():
    """M20. Once a recording carries `channel_display` at all, a MISSING entry for
    a sense it draws is an error, not a licence to invent positional names --
    "Channel 0" on an enabled sense is the one name this module promises can
    never reach a frame."""
    with pytest.raises(KeyError) as exc:
        LB.ChannelDisplay.from_meta("Visual", 8, None, key_present=True)
    assert "Visual" in str(exc.value)


# ---------------------------------------------------------------------------
# 6. reading the config -- no fallback defaults
# ---------------------------------------------------------------------------
def _resolved(**overrides):
    from src.environment.config_loader import load_env_config, load_env_params

    cfg = load_env_config(str(_ROOT / "configs/environment/default.yaml"))
    for k, v in overrides.items():
        cfg.set(k.replace("__", "."), v)
    return cfg, load_env_params(cfg)


@pytest.mark.parametrize("key", [
    "sensory.olfactory_channel_names",
    "sensory.olfactory_channel_groups",
    "sensory.visual_channel_names",
    "sensory.visual_channel_groups",
])
def test_a_missing_display_key_raises_naming_that_key(key):
    """One test per new key, per the CONFIG_GUIDE Maintenance Contract. A missing
    key must raise naming the key -- never a silent default, which would let a
    pre-change run record today's names as though it had declared them."""
    from src.utils.eval_recording import channel_display_from_config

    cfg, params = _resolved()
    cfg.set(key, None)
    with pytest.raises(ValueError) as exc:
        channel_display_from_config(cfg, params)
    assert key in str(exc.value)


def test_the_missing_key_error_teaches_rather_than_just_reporting():
    """D7: this fires for every checkpoint trained before this change, so the
    message names the remedy instead of a bare "key required but missing"."""
    from src.utils.eval_recording import channel_display_from_config

    cfg, params = _resolved()
    cfg.set("sensory.visual_channel_names", None)
    with pytest.raises(ValueError) as exc:
        channel_display_from_config(cfg, params)
    msg = str(exc.value).lower()
    assert "re-record" in msg or "record" in msg
    assert "predate" in msg or "before" in msg


def test_the_shipped_default_config_records_a_valid_display():
    from src.utils.eval_recording import channel_display_from_config

    cfg, params = _resolved()
    payload = channel_display_from_config(cfg, params)
    assert set(payload) == {"Olfaction", "Visual"}
    assert len(payload["Olfaction"]["names"]) == int(params.olfactory_vector_size)
    assert len(payload["Visual"]["names"]) == int(params.visual_vector_size)
    # it must survive the reader it was written for
    for sense, n in (("Olfaction", params.olfactory_vector_size),
                     ("Visual", params.visual_vector_size)):
        d = LB.ChannelDisplay.from_meta(sense, int(n), payload[sense], key_present=True)
        assert d.legacy is False


def test_a_names_list_that_disagrees_with_the_configs_own_width_raises():
    from src.utils.eval_recording import channel_display_from_config

    cfg, params = _resolved()
    cfg.set("sensory.visual_channel_names", _names(4))
    with pytest.raises(ValueError) as exc:
        channel_display_from_config(cfg, params)
    msg = str(exc.value)
    assert "4" in msg and str(int(params.visual_vector_size)) in msg


# ---------------------------------------------------------------------------
# 7. the enabled-sense rule (a sense that is OFF needs no names)
# ---------------------------------------------------------------------------
def test_a_disabled_sense_needs_no_names_and_gets_no_entry():
    """User decision, 2026-09-21. Demanding vision names from a vision-off config
    would fail on a correct file -- and giving it eight names for a sense that is
    switched off is exactly the quiet mistake this change exists to remove."""
    from src.utils.eval_recording import channel_display_from_config

    cfg, params = _resolved(sensory__visual_sensor_enabled=False)
    assert bool(params.visual_sensor_enabled) is False
    cfg.set("sensory.visual_channel_names", None)
    cfg.set("sensory.visual_channel_groups", None)
    payload = channel_display_from_config(cfg, params)   # must not raise
    assert set(payload) == {"Olfaction"}


def test_display_keys_for_a_disabled_sense_are_ignored_not_refused():
    """There is no resolved width to validate a length against, and refusing
    would punish a harmless leftover."""
    from src.utils.eval_recording import channel_display_from_config

    cfg, params = _resolved(sensory__visual_sensor_enabled=False)
    cfg.set("sensory.visual_channel_names", _names(99))
    payload = channel_display_from_config(cfg, params)   # must not raise
    assert "Visual" not in payload


def test_a_vision_off_context_builds_no_vision_display(caplog):
    """M23. The display is built only for senses the world actually observes. An
    EAGER per-sense build would raise on a perfectly good vision-off recording,
    because its payload legitimately has no `Visual` entry."""
    ctx = P.LayoutContext(
        world_w=10, world_h=10, local_view_size=5,
        breakdown={"Satiation": 1, "Olfaction": 5 * P._diamond_cells(1),
                   "Collision": 5, "Proprioception": 4},
        thermal=False, intero_noc_enabled=False,
        olfactory_range=1, visual_range=0,
        visual_vector_size=1, olfactory_channels=5,
        channel_display={"Olfaction": _payload(5)},     # NO "Visual" entry
    )
    P.check_completeness(ctx)
    cards = P.present_cards(ctx, band=True)              # must not raise
    assert any(c.key == "band" for c in cards)
    assert ctx.display_for("Olfaction").legacy is False

"""What a sense's channels are CALLED, and how many map slots its panel holds.

PLAIN-LANGUAGE SUMMARY. The episode video draws one small map per sensor channel
and prints that channel's name underneath it -- "Food", "Predator", "Terrain".
This module answers two questions about that strip of maps: what each one is
called, and how many of them the panel is sized for.

NAMES ARE DATA NOW, NOT A TABLE IN HERE. Until 2026-09-21 this module held the
names themselves, keyed by channel index. It no longer does, and the tables are
deleted rather than deprecated. A channel's name comes from the environment
config, is validated against the run's real channel count when the recording is
written, and travels with the recording in `run_meta.pkl`. So there is exactly
ONE place a name can come from.

WHY THAT MATTERED ENOUGH TO DELETE WORKING CODE. A name that exists in two
places is a name that can disagree with itself, and this renderer lost precisely
that bet: the panel-width bug of 2026-09-18 was two modules holding two different
answers to one question -- how many maps vision draws -- and every video failed
to render. That one was about a COUNT, so it crashed. A display NAME that
silently disagrees with the channel it labels is worse, because nothing crashes:
the video just tells its reader that a channel means something it does not.

THE PANEL IS A FIXED SIZE, AND THE BLANK SPACE IS INTENDED. `PANEL_MAP_SLOTS`
below is a conventional SIZE, not a limit. How many channels a sense has is a
deliberate experimental knob here -- one study runs vision at a single channel --
and a panel that resized itself to the live count would draw a differently shaped
video for every arm, which is exactly what makes two runs incomparable. So the
panel keeps its width whatever the run declares, and a run with fewer channels
leaves part of it blank. THAT BLANK AREA IS NOT A LAYOUT BUG. See `D4b` in
`docs/develop/active/refactors/DASHBOARD_CHANNEL_NAMES_FROM_CONFIG.md` before
"fixing" it.

AND A RUN WITH MORE MAPS THAN SLOTS DRAWS PAST THE PANEL EDGE. That is a user
decision taken on 2026-09-19, chosen over shrinking the slots to fit (which
reintroduces the count-dependent sizing this design removes) and over refusing
the config. Nothing raises; a warning naming both numbers is logged when the
display is built, so an accidental edit -- deleting the Terrain group takes
vision from 6 maps to 8 -- is discoverable instead of silent.

NO MATPLOTLIB, DELIBERATELY. The layout registry imports this module and must
stay importable without a drawing library (a test pins it), because layout runs
once per episode before any figure exists. `palette` is imported for the terrain
colours' ARITY only, and is itself nothing but colour strings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping

from .palette import TERRAIN_FILL

logger = logging.getLogger(__name__)

#: The observation-breakdown names this module knows. These are the environment's
#: own keys, not the reader-facing titles -- the band's vision card is titled
#: "Vision" on screen while the sense it looks values up under stays "Visual".
SENSES = ("Olfaction", "Visual")

#: How many map slots a sense's panel is sized for, whatever the run's channel
#: count. This is the number of maps the CONVENTIONAL world draws: smell's five
#: channels are five maps, and vision's eight channels are six maps because the
#: three terrain channels ship merged into one. It is a conventional SIZE and NOT
#: a limit: the panel keeps this width whatever the run declares, so a run drawing
#: more maps than there are slots draws them PAST THE PANEL EDGE rather than being
#: refused or resized (user decision, 2026-09-19 -- see D4b before "fixing" an
#: overlapping frame). Raising it is a one-line edit here.
#:
#: WHY THIS IS IN MAPS AND NOT IN CHANNELS. The panel is laid out in maps, and
#: vision's eight channels draw six maps because three of them merge. Sizing in
#: channels would make the vision panel a third wider than anything drawn into
#: it -- which is the precise miscount that broke every video in `4b6f7196`.
PANEL_MAP_SLOTS = {"Olfaction": 5, "Visual": 6}

#: How many channels a single merged map can colour. The merged map is drawn in
#: flat per-channel colours from `palette.TERRAIN_FILL`, so a group with more
#: members than there are colours has no colour for its last one. Read from the
#: palette rather than written down again, so the two cannot drift.
TERRAIN_PALETTE_ARITY = len(TERRAIN_FILL)


def _check_sense(sense: str) -> None:
    if sense not in PANEL_MAP_SLOTS:
        raise KeyError(
            f"no channel display for sense {sense!r}; known senses are "
            f"{list(PANEL_MAP_SLOTS)}"
        )


def validate_entry(sense: str, n_channels: int, entry: Mapping, *, where: str = ""):
    """Validate one sense's ``{names, groups}`` payload; return it as tuples.

    Shared by the READER (:meth:`ChannelDisplay.from_meta`, which sees a payload
    unpickled from a recording) and the WRITER
    (``eval_recording.channel_display_from_config``, which sees one just built
    from a config), so the two can never enforce different rules.

    Every failure raises ``ValueError`` naming BOTH numbers involved -- what was
    declared and what the run actually has -- because "length mismatch" without
    the numbers makes the reader go and measure them by hand.
    """
    _check_sense(sense)
    at = f" ({where})" if where else ""

    if not isinstance(entry, Mapping):
        raise ValueError(
            f"{sense} channel display{at} must be a mapping with 'names' and "
            f"'groups'; got {type(entry).__name__}")

    raw_names = entry.get("names")
    if raw_names is None:
        raise ValueError(f"{sense} channel display{at} carries no 'names' list")
    raw_names = list(raw_names)

    if len(raw_names) != int(n_channels):
        raise ValueError(
            f"{sense} declares {len(raw_names)} channel names{at} but this run has "
            f"{int(n_channels)} {sense} channels. The names list must have exactly "
            f"one entry per channel -- a config that sets its own sense width must "
            f"redeclare that sense's names in the SAME file, because a child config "
            f"replaces a list wholesale or not at all and cannot shorten an "
            f"inherited one.")

    names = []
    for i, item in enumerate(raw_names):
        if isinstance(item, Mapping):
            name, qualifier = item.get("name"), item.get("qualifier", "")
        else:
            name, qualifier = item, ""
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"{sense} channel {i}{at} has no usable name (got {name!r}). Every "
                f"channel needs a non-empty name: the rendered frame is the only "
                f"surface a viewer has, and it carries no key to an index.")
        if qualifier is None:
            qualifier = ""
        if not isinstance(qualifier, str):
            raise ValueError(
                f"{sense} channel {i}{at}: qualifier must be a string, got "
                f"{qualifier!r}. Name and qualifier are two FIELDS, never one "
                f"string -- the painter must not have to parse its own label text.")
        names.append((name, qualifier))

    groups, claimed = [], {}
    for g in list(entry.get("groups") or []):
        if isinstance(g, Mapping):
            gname, channels = g.get("name"), g.get("channels")
        else:
            gname, channels = g[0], g[1]
        if not isinstance(gname, str) or not gname.strip():
            raise ValueError(f"{sense} declares a channel group{at} with no name")
        channels = tuple(int(c) for c in (channels or ()))

        if len(channels) < 2:
            raise ValueError(
                f"{sense} group {gname!r}{at} covers {len(channels)} channel(s). A "
                f"group draws several channels as ONE map, so it needs at least 2; "
                f"a group of one is a plain channel wearing a group's name.")
        if len(channels) > TERRAIN_PALETTE_ARITY:
            raise ValueError(
                f"{sense} group {gname!r}{at} covers {len(channels)} channels but "
                f"the merged map has only {TERRAIN_PALETTE_ARITY} colours to draw "
                f"them in. Refused rather than silently reusing a colour, which "
                f"would make two different channels look identical on the frame.")
        for c in channels:
            if not 0 <= c < int(n_channels):
                raise ValueError(
                    f"{sense} group {gname!r}{at} names channel {c}, but this run "
                    f"has {int(n_channels)} {sense} channels (valid: 0..."
                    f"{int(n_channels) - 1}).")
            if c in claimed:
                raise ValueError(
                    f"{sense} channel {c}{at} appears in two groups "
                    f"({claimed[c]!r} and {gname!r}); a channel may be drawn on one "
                    f"map only.")
            claimed[c] = gname
        if len(set(channels)) != len(channels):
            raise ValueError(
                f"{sense} group {gname!r}{at} repeats a channel: {channels}")
        if tuple(sorted(channels)) != tuple(range(min(channels), max(channels) + 1)):
            raise ValueError(
                f"{sense} group {gname!r}{at} covers {channels}, which is not a "
                f"contiguous run of channels. The merged map is drawn at the "
                f"position of the group's first channel, so a gapped group has no "
                f"well-defined place in the strip.")
        groups.append((gname, tuple(channels)))

    return tuple(names), tuple(groups)


@dataclass(frozen=True)
class ChannelDisplay:
    """Everything the renderer needs to LABEL one sense.

    Built from a recording's ``run_meta['channel_display']``, or positionally
    when the recording predates it.
    """

    names: tuple[tuple[str, str], ...]          # (name, qualifier) per channel
    groups: tuple[tuple[str, tuple[int, ...]], ...]
    legacy: bool                                 # True -> positional names, no groups

    @classmethod
    def from_meta(cls, sense: str, n_channels: int, meta_entry, *,
                  key_present: bool) -> "ChannelDisplay":
        """Build one sense's display from a recording's payload.

        ``key_present`` is whether ``run_meta`` carried a top-level
        ``channel_display`` AT ALL -- **not** whether this sense has an entry in
        it. The two stopped being the same thing when names became required only
        for ENABLED senses: a perfectly good configured recording legitimately
        has no ``Visual`` entry, because that run had vision switched off.

        Keying "legacy" off the per-sense entry instead would hand positional
        names to three unlike cases -- a pre-change recording, a disabled sense,
        and a forgotten or hand-edited entry -- and the third would silently ship
        "Channel 0" on an ENABLED sense, which is the one name this module
        promises can never reach a frame.
        """
        _check_sense(sense)
        n = int(n_channels)
        if not key_present:
            # Genuinely pre-change: no names anywhere, so positional ones, and no
            # groups -- the terrain merge is data this recording does not carry.
            return cls(tuple((f"Channel {i}", "") for i in range(n)), (), True)
        if meta_entry is None:
            raise KeyError(
                f"run_meta carries channel_display but has no entry for {sense!r}, "
                f"which is enabled on this recording. A configured recording must "
                f"name every sense it draws. Re-record it at current code.")
        names, groups = validate_entry(sense, n, meta_entry, where="run_meta")
        return cls(names, groups, False)


def map_plan(sense: str, display: ChannelDisplay) -> list:
    """Which maps a sense draws: ``[(name, qualifier, kind, channels), ...]``.

    A grouped run of channels becomes ONE map of kind ``"terrain"``; every other
    channel is its own ``"seq"`` map at its own index. A group is drawn at the
    position of its first channel.

    THE LAST ELEMENT CARRIES THE GROUP'S OWN CHANNEL TUPLE -- an int for a plain
    channel, the declared tuple for a group. The painter must read exactly these
    and never a literal slice: a group is DATA now, so a hardcoded ``row[:3]``
    would colour ``{Terrain, [1,2,3]}`` from channels 0-2 with no error at all.
    That defect would have validated, placed the map correctly, and drawn the
    wrong picture in silence.

    WHY THIS LIVES IN `labels` RATHER THAN IN THE PAINTER THAT DRAWS FROM IT
    (moved 2026-09-18). Two modules need this answer and they must never give
    different ones: the painter draws the maps, and the layout registry
    (`panels._span`) has to declare how much room they need BEFORE any of them is
    drawn. While the count lived in the painter, the registry could not ask for
    it -- `panels` must stay importable without Matplotlib -- so it counted
    CHANNELS instead and declared a vision panel a third wider than the painter
    has ever needed, and the packer refused to lay out a frame that draws.
    """
    _check_sense(sense)
    starts = {chans[0]: (name, chans) for name, chans in display.groups}
    covered = {c for _, chans in display.groups for c in chans}

    out = []
    for i, (name, qualifier) in enumerate(display.names):
        if i in starts:
            gname, chans = starts[i]
            out.append((gname, "", "terrain", tuple(chans)))
            continue
        if i in covered:
            continue
        out.append((name, qualifier, "seq", i))
    return out


def panel_map_slots(sense: str, display: ChannelDisplay) -> int:
    """How many slots the panel is sized for.

    The fixed conventional size, EXCEPT that a legacy recording is sized to what
    it actually draws. That asymmetry is deliberate and load-bearing: a legacy
    8-channel recording carries no merge group, so it draws 8 maps, and forcing
    it into the conventional 6 would overflow EVERY recording already on disk,
    including all eleven render-audit fixture cells. The fixed width applies to
    recordings written after channel names existed, where a config genuinely
    declared the count. The obvious "simplification" -- using the constant
    everywhere -- silently breaks every archived recording.

    Deliberately does NOT raise when a configured run draws more maps than there
    are slots: no limit is imposed (user decision). It WARNS, naming both
    numbers, so an accidental edit -- deleting the Terrain group takes vision
    from 6 maps to 8 -- is discoverable instead of silent.
    """
    _check_sense(sense)
    drawn = len(map_plan(sense, display))
    slots = PANEL_MAP_SLOTS[sense]
    if display.legacy:
        return max(slots, drawn)
    if drawn > slots:
        logger.warning(
            "%s draws %d maps but its panel has %d slots; the extra maps will be "
            "drawn past the panel edge. This is allowed and nothing is refused -- "
            "if it was not intended, check sensory.%s_channel_groups.",
            sense, drawn, slots,
            "visual" if sense == "Visual" else "olfactory")
    return slots

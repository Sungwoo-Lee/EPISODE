"""V2-owned channel label table.

WHY THIS EXISTS. ``src/environment/sensor.py::build_sensory_viz`` emits its own
``labels`` field, and one of those labels is wrong for a reader: the hiding
predator's visual channel is labelled ``DNG`` ("danger"), which names a judgement
rather than the thing sensed. ``sensor.py`` is a frozen file for the whole of
this plan (it is on the V1 video path), so the label is corrected *here*, in a
table the new renderer owns and which overrides the adapter's labels. V1 frames
keep ``DNG`` until the retirement gate, which is deliberate -- it keeps the V1
byte-identity guard meaningful.

SCOPE RULE (plan section D7.7 item 6). The named table applies **only** when the
visual property vector is the standard 8 channels. Any other width gets
positional ``C0 ... C{V-1}`` labels, because a name table keyed by index is a
lie as soon as the channel layout changes.
"""

from __future__ import annotations

# Olfactory spectrum components. AN-A / AN-B are two *shared* animal-odour
# components -- predators load mostly on A and neutral animals mostly on B, with
# heavy overlap -- so they are named by their leaning and never "Predator" /
# "Neutral", which would claim a separation the signal does not have.
OLFACTORY_LABELS: tuple[str, ...] = ("FOOD", "AN-A", "AN-B", "BUSH", "TREE")

OLFACTORY_LONG: dict[str, str] = {
    "FOOD": "Food",
    "AN-A": "Odour A (predator-leaning)",
    "AN-B": "Odour B (neutral-leaning)",
    "BUSH": "Bush",
    "TREE": "Tree",
}

# The standard 8-channel visual property vector: three terrain channels then
# five entity channels. Channel 6 is shared by every obstacle (rock, bush,
# campfire), so it is "Obstacle" and not "Rock".
VISUAL_LABELS_V8: tuple[str, ...] = (
    "GRS",
    "SND",
    "PLN",
    "FOD",
    "HPR",
    "PRD",
    "RCK",
    "NEU",
)

VISUAL_LONG: dict[str, str] = {
    "GRS": "Grass",
    "SND": "Sand",
    "PLN": "Plain",
    "FOD": "Food",
    "HPR": "Hiding predator",
    "PRD": "Predator",
    "RCK": "Obstacle",
    "NEU": "Neutral",
}

#: The label this package refuses to inherit from the frozen adapter, kept
#: named so a test can assert the override actually happened.
SUPERSEDED_VISUAL_LABELS: dict[str, str] = {"DNG": "HPR"}

_STANDARD_VISUAL_WIDTH = 8


def visual_labels(visual_vector_size: int) -> tuple[str, ...]:
    """Short labels for the visual channels, or positional names off-standard."""
    if visual_vector_size == _STANDARD_VISUAL_WIDTH:
        return VISUAL_LABELS_V8
    return tuple(f"C{i}" for i in range(visual_vector_size))


def olfactory_labels(n_channels: int) -> tuple[str, ...]:
    """Short labels for the olfactory components, or positional names off-standard."""
    if n_channels == len(OLFACTORY_LABELS):
        return OLFACTORY_LABELS
    return tuple(f"C{i}" for i in range(n_channels))


def channel_labels(sense: str, n_channels: int) -> tuple[str, ...]:
    """Short labels for ``sense``'s channels.

    ``sense`` is a breakdown name -- ``"Visual"`` or ``"Olfaction"``.
    """
    if sense == "Visual":
        return visual_labels(n_channels)
    if sense == "Olfaction":
        return olfactory_labels(n_channels)
    raise KeyError(
        f"no channel label table for sense {sense!r}; "
        f"known senses are 'Visual' and 'Olfaction'"
    )

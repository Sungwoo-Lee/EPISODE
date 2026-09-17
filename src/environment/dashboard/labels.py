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

TWO NAMESPACES, AND WHY THEY ARE BOTH RIGHT. This module names **sensor
channels** (``FOD``, ``AN-A``, ``GRS``); ``cells.DISPLAY_NAME`` names **the
things drawn in a world square** (``neutral`` -> "rabbit"). They are deliberately
separate tables because they answer different questions, and the one place they
appear to disagree is real rather than an oversight: the visual channel ``NEU``
is "Neutral", because the channel is the *property axis* an observation carries,
while the animal standing in a square is a "rabbit". Nothing may add a THIRD
table -- a surface that shows a channel to a reader calls :func:`display_channel`
here, and a surface that names an occupant calls ``cells.display`` there.

THE RULE THIS MODULE EXISTS TO ENFORCE, AS OF 2026-09-17. The short codes are an
internal index, never a thing a viewer reads. The renderer used to print them
straight onto the frame -- a smell panel labelled ``AN-A`` / ``BUSH`` and a
vision panel labelled ``FOD`` / ``HPR`` / ``RCK`` -- so the dashboard asked its
reader to learn an eight-entry abbreviation table that exists nowhere on the
page. :func:`display_channel` is the only way a channel name reaches a frame,
and it raises on an unknown code rather than passing it through, because a code
that leaks to the page is exactly the defect being removed. The one deliberate
exception is the collision diamond's C/U/R/D/L, which are positions rather than
entities and are glossed in that card's own subtitle.
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

#: The same five names, split into the part that identifies the channel and the
#: part that qualifies it. The approved design sets the qualifier in a lighter,
#: smaller style beside the name rather than in brackets after it, so the panel
#: reads "Odour A  predator-leaning" -- and a painter cannot produce that from
#: ``OLFACTORY_LONG``'s single string without parsing its own label text, which
#: is how a display detail turns into a parser. Derived from the table above at
#: import, so the two can never drift.
OLFACTORY_PARTS: dict[str, tuple[str, str]] = {
    code: (name.split(" (", 1)[0], name.split(" (", 1)[1].rstrip(")")
           if " (" in name else "")
    for code, name in OLFACTORY_LONG.items()
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

    These are the INTERNAL codes. Nothing that a viewer reads may use them
    directly -- see :func:`display_channel`.
    """
    if sense == "Visual":
        return visual_labels(n_channels)
    if sense == "Olfaction":
        return olfactory_labels(n_channels)
    raise KeyError(
        f"no channel label table for sense {sense!r}; "
        f"known senses are 'Visual' and 'Olfaction'"
    )


def display_channel(sense: str, code: str) -> tuple[str, str]:
    """The ``(name, qualifier)`` a READER sees for one sensor channel.

    ``qualifier`` is the empty string for every channel but the two shared
    animal odours, whose leaning is the whole reason they are not called
    "Predator" and "Neutral".

    Raises rather than falling back to the code. A silently passed-through
    ``AN-A`` on a rendered frame is the defect this function exists to make
    loud: the frame is the only surface a viewer has, and it carries no key to
    an abbreviation table.
    """
    if sense == "Olfaction":
        table, parts = OLFACTORY_LONG, OLFACTORY_PARTS
        if code in parts:
            return parts[code]
    elif sense == "Visual":
        table = VISUAL_LONG
        if code in table:
            return (table[code], "")
    else:
        raise KeyError(
            f"no channel label table for sense {sense!r}; "
            f"known senses are 'Visual' and 'Olfaction'"
        )
    # A positional C0/C1/... code is produced on purpose when the vector width is
    # off-standard (the SCOPE RULE above), and it is the one thing a reader may
    # legitimately be shown without a name, because no name table applies.
    if code.startswith("C") and code[1:].isdigit():
        return (f"Channel {code[1:]}", "")
    raise KeyError(
        f"no reader's name for {sense} channel {code!r}; known codes are "
        f"{sorted(table)}. A channel code must never reach a rendered frame: the "
        f"frame carries no key to it."
    )

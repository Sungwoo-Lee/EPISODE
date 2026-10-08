"""Shared helpers for the AI-consciousness field-review figures.

ONE COLOUR, ONE MEANING, PER PAGE (format register F11 amendment). On this page:
  * blue / orange  -> a reply's verdict on Seth's thesis: blue supports, orange rejects, with the two
    middle verdicts in ink greys (figure 3 only);
  * everything else is drawn in ink greys, glyphs and line styles.
So the page chrome is de-hued (--accent set to ink), because blue and orange carry data here.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
DATA = os.path.join(HERE, "..", "field_data")
FIGS = os.path.join(HERE, "figures")
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house  # noqa: E402

VERDICTS = [("supports", "supports Seth", house.BLUE),
            ("extends", "extends his case", "#7f8a96"),
            ("qualifies", "qualifies it", "#b9bfc6"),
            ("rejects", "rejects it", house.ORANGE)]


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        raise SystemExit(f"missing data file {path} - run field_data/build_field_data.py")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def note(stem, text):
    """A one-line source note the page prints under the figure (written by the script, never typed)."""
    os.makedirs(FIGS, exist_ok=True)
    with open(os.path.join(FIGS, f"{stem}.data.txt"), "w") as fh:
        fh.write(text.strip() + "\n")

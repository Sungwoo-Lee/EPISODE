"""Calibration tests for scripts/eval/render_layout_audit.py (RENDERER_LAYOUT_REDESIGN CP0.3).

The audit is the instrument the whole redesign is measured with, so what is under test
here is not "does it run". It is four separate questions:

  * does it find the defects we already know are there, FOR THE RIGHT REASON and AT THE
    RIGHT PLACE in the frame (positive controls, with coordinates pinned);
  * would it stop finding them if the measurement broke (mutation control on the
    threshold);
  * could it be replaced by an instrument that simply says YES TO EVERYTHING without any
    test noticing (negative controls — exact absent-panel set, exact per-rule counts,
    and the rules that must stay SILENT — plus a mutation that makes `FrameProbe.ink()`
    return all-True and asserts the calibrated counts break);
  * do the bugs found in the instrument while calibrating it stay fixed (one regression
    test per bug, at unit level where the helper can be reached and at frame level where
    it cannot).

The third question is the one this file exists for. An earlier version of it passed in
full against an `ink()` that flagged every pixel of the canvas — every positive control
still "fired", because a control only asks whether a finding appeared. A control set can
only ever measure sensitivity; discrimination has to be measured by pinning what is NOT
found.

Fixtures live under gitignored `results/`, so the integration tests SKIP with an explicit
reason when they are absent rather than passing vacuously.
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "scripts" / "eval"))
import render_layout_audit as audit  # noqa: E402

FIXTURES = _REPO / audit.DEFAULT_FIXTURE_ROOT
_MISSING = f"render-audit fixtures not on disk ({FIXTURES}); regenerate with " \
           f"scripts/eval/make_render_fixture_recordings.py"


def _have(cell="M4"):
    d = FIXTURES / cell / cell
    return d.is_dir() and any(d.glob("episode_*.rec.gz"))


# --------------------------------------------------------------- calibrated ground truth
#
# Exact, measured expectations on two frozen frames. EXACT rather than lower bounds, on
# purpose: V1 is a frozen file (§D5.4) and the fixtures are pinned by v1_path_guard's raw
# frame hashes, so any movement in these numbers is either a change to a frozen renderer
# or a change in the instrument — and both must be seen, not absorbed.
#
# Every entry below was measured from the audit's own output on 2026-09-16 and traced to a
# numbered defect: M4's text_over_text is D1, its out_of_card is D2, one of its three
# text_over_border hits is D3, its panel_absent is D12, its four observed_caption hits are
# D10 (Nutrition and Injury, OBS and REAL each); M1's four text_over_text hits are D5
# (three) plus the same extero readout escape that gives D1 on M4.
V1_M4_COUNTS = {
    "text_over_text": 1,
    "text_over_border": 3,
    "text_over_fill": 5,
    "fill_over_text": 1,
    "out_of_card": 1,
    "panel_absent": 1,
    "observed_caption": 4,
}
V1_M1_COUNTS = {
    "text_over_text": 4,
    "text_over_border": 2,
    "out_of_card": 1,
    "panel_absent": 1,
    "observed_caption": 4,
}
# Rules that must stay SILENT on both calibrated frames. An instrument that flagged
# everything could not keep any of them silent, which is exactly the point of listing them.
SILENT_RULES = ("clipped", "out_of_canvas", "legibility", "numeric_in_arena",
                "fill_over_text")

# Coordinates, in image pixels from the top-left, of every control hit.
#   (rule, token in `a`, token in `b` or None, expected overlap px or 0, expected bbox)
# Tolerance: +/- BBOX_TOL_PX on each bbox coordinate and +/- PX_TOL on the overlap. The
# frames are byte-pinned by the guard on this machine, so the honest tolerance is zero; a
# couple of pixels are allowed only for freetype hinting differences on another machine.
# It is far tighter than any relocation: a collision that moved to a different element or
# a different panel moves by tens to hundreds of pixels.
CONTROL_COORDS = {
    "D1": [("text_over_text", "OBS:", "THERMOCEPTION", 59, (1179, 357, 1230, 359))],
    "D2": [("out_of_card", "REAL:", "EXTERO NOCICEPTION", 169, (1183, 279, 1228, 286))],
    "D3": [("text_over_border", "MINIMAP", None, 30, (252, 644, 295, 644))],
    "D6": [("text_over_text", "COLLISION", "'C'", 17, (1117, 453, 1122, 457)),
           ("text_over_text", "COLLISION", "'U'", 25, (1179, 453, 1184, 457))],
    # The token carries the VALUE drawn on the frame, so it moves when the fixture world
    # does. Re-pinned 2026-09-16 (0.13 -> 0.65) for the demonstration loosening applied in
    # make_render_fixture_recordings.py (_DEMO_LOOSENING), which raises the episode's start
    # nutrition. The bbox is unchanged, which is the part that says the defect has not moved.
    "D10": [("observed_caption", "OBS:  0.65", "Nutrition", 0, (316, 292, 365, 298))],
}
BBOX_TOL_PX = 2
PX_TOL_FRAC = 0.2


def _bbox_close(got, want):
    return got is not None and all(abs(int(g) - w) <= BBOX_TOL_PX
                                   for g, w in zip(got, want))


def _px_close(got, want):
    return abs(int(got) - want) <= max(3, round(PX_TOL_FRAC * want))


# ------------------------------------------------------------------ import isolation


def test_audit_imports_neither_layout_nor_registry():
    """§D5.2: the audit must not import the thing it audits.

    THE LEAK CHECK RUNS IN A SUBPROCESS, and that is the point of it. `sys.modules`
    is process-global, so measuring it in-process measures what the WHOLE pytest
    session imported, not what the audit imported. That was a valid proxy only
    while no renderer package existed: once Phase 1 added
    `src/environment/dashboard/`, `test_dashboard_layout.py` — which sorts before
    this file — imported it and left it there, and this test went red on a
    full-directory run while still passing when run alone. The failure was in the
    *measurement*, not in the audit, whose real isolation never changed.

    A subprocess restores the property the assertion needs — that the only thing
    which could have imported the package is the audit itself — and it does so
    WITHOUT weakening what is asserted, which stays "not one module of it, by
    exact list". The assertion is what keeps the instrument from sharing code with
    the thing it measures, so an allow-list or a substring exemption that made the
    red go away would be worse than the red. The same subprocess pattern is used
    by `test_dashboard_layout.py::test_the_package_imports_without_matplotlib`.

    The probe is checked for BLINDNESS in the same subprocess: after taking the
    measurement it imports the package on purpose and measures again. A probe that
    cannot see the package even when handed it would report "no leak" forever —
    if the package were renamed, moved, or became unimportable — and an empty
    result from a blind probe is evidence of nothing.
    """
    probe = textwrap.dedent(
        """
        import json, os, sys
        root = os.getcwd()
        sys.path.insert(0, os.path.join(root, "scripts", "eval"))

        def leaked():
            return sorted(m for m in sys.modules if "environment.dashboard" in m)

        import render_layout_audit  # noqa: F401
        after_audit = leaked()
        sys.path.insert(0, root)
        import src.environment.dashboard  # noqa: F401
        print(json.dumps({"after_audit": after_audit, "after_forced": leaked()}))
        """
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_REPO, capture_output=True, text=True
    )
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout.strip().splitlines()[-1])
    assert got["after_audit"] == [], (
        f"audit pulled in the renderer package under test: {got['after_audit']}")
    assert got["after_forced"], (
        "the leak probe reported nothing even after the renderer package was "
        "imported on purpose, so it cannot detect a leak at all and the empty "
        "measurement above means nothing")

    src = (_REPO / "scripts" / "eval" / "render_layout_audit.py").read_text()
    for banned in ("from src.environment.dashboard", "import src.environment.dashboard"):
        assert banned not in src


# ------------------------------------------------------------------------- helpers


def test_dilate_grows_by_one_pixel():
    m = np.zeros((5, 5), dtype=bool)
    m[2, 2] = True
    assert audit._dilate(m).sum() == 5          # the pixel plus its four neighbours


def test_rect_mask_flips_display_y_to_image_rows():
    m = audit._rect_mask(10, 10, 0, 0, 10, 2)   # bottom two rows in display coords
    assert m[8:].all() and not m[:8].any()


def test_ink_is_outline_separates_a_frame_from_a_fill():
    bbox = (0, 0, 20, 20)
    hollow = np.zeros((20, 20), dtype=bool)
    hollow[0, :] = hollow[-1, :] = hollow[:, 0] = hollow[:, -1] = True
    solid = np.ones((20, 20), dtype=bool)
    assert audit._ink_is_outline(hollow, bbox, 20)
    assert not audit._ink_is_outline(solid, bbox, 20)


def test_normalise_title_strips_the_rendered_suffixes():
    assert audit._normalise_title("COLLISION  (OBS ONLY)") == "COLLISION"
    assert audit._normalise_title("Extero Nociception") == "EXTERO NOCICEPTION"


def test_title_name_matches_a_caption_that_carries_its_scale():
    """Instrument bug 3: V1's gauge is labelled `BODY TEMP   DIE -15 / +15`.

    An exact-match title table reported that drawn panel as SILENTLY DROPPED — the one
    verdict the panel_absent rule exists to give, delivered wrongly.
    """
    assert audit._title_name("BODY TEMP   DIE -15 / +15") == "Body Temperature"
    assert audit._title_name("SATIATION") == "Satiation"
    assert audit._title_name("OBS:  0.00") is None


def test_control_matcher_rejects_the_right_rule_on_the_wrong_elements():
    """'Fires for the wrong reason' must count as not firing."""
    ctl = audit.CONTROLS["D1"]
    right = audit.Finding("text_over_text", "", "text 'OBS:  0.00'",
                          "text 'THERMOCEPTION (OBS ONLY)'", 59, None)
    wrong_partner = audit.Finding("text_over_text", "", "text 'OBS:  0.00'",
                                  "text 'COLLISION'", 59, None)
    wrong_rule = audit.Finding("text_over_fill", "", "text 'OBS:  0.00'",
                               "text 'THERMOCEPTION (OBS ONLY)'", 59, None)
    assert audit._control_matches(ctl, right)
    assert not audit._control_matches(ctl, wrong_partner)
    assert not audit._control_matches(ctl, wrong_rule)


def test_d2_control_does_not_carry_an_unreachable_rule():
    """`text_over_border` was removed from D2's accepted rules as DEAD, not as strict.

    A border finding names its partner `patch Rectangle in axes@NNNN` — the axes' name —
    so D2's `b_contains: 'EXTERO NOCICEPTION'` could never match one. Keeping it would
    advertise a fallback that cannot fire. `text_over_text` stays, because that IS the
    class the defect would take if the renderer's 1.55 px gap ever closed.
    """
    rules = audit.CONTROLS["D2"]["rules"]
    assert "out_of_card" in rules and "text_over_text" in rules
    assert "text_over_border" not in rules
    border_finding = audit.Finding("text_over_border", "", "text 'REAL: --'",
                                   "patch Rectangle in axes@224", 12, None)
    assert not audit._control_matches(audit.CONTROLS["D2"], border_finding)


def test_no_required_controls_subset_exists():
    """`main()` fails on ANY missed control, so a 'required five' constant would lie."""
    assert not hasattr(audit, "REQUIRED_CONTROLS")
    assert set(audit.CONTROLS) == {"D1", "D2", "D3", "D6", "D8", "D10", "D12"}


# ------------------------------------------- instrument-bug regressions, at unit level


class _FakeAx:
    """Just enough Axes for the draw-order helper: an ordered child list."""

    def __init__(self):
        self._children = []

    def get_children(self):
        return list(self._children)


class _FakeArtist:
    def __init__(self, ax=None, zorder=1.0):
        self.axes = ax
        self._z = zorder
        if ax is not None:
            ax._children.append(self)

    def get_zorder(self):
        return self._z


class _FakeProbe:
    """Serves precomputed ink masks, so a helper can be tested without rendering."""

    def __init__(self, h, w, inks):
        self.h, self.w, self._inks = h, w, inks

    def ink(self, el):
        return self._inks[id(el.artist)]


def _outline_ink(h, w, bbox):
    """Ink on the PERIMETER of a display-coordinate box, as a real card lays down."""
    m = np.zeros((h, w), dtype=bool)
    x0, y0, x1, y1 = (int(round(v)) for v in bbox)
    r0, r1 = h - y1, h - y0                      # display y (up) -> image rows (down)
    m[r0:r1, x0:x0 + 1] = True
    m[r0:r1, x1 - 1:x1] = True
    m[r0:r0 + 1, x0:x1] = True
    m[r1 - 1:r1, x0:x1] = True
    return m


def test_title_strip_is_bounded_to_one_title_line():
    """Instrument bug 2: the title-strip rule invented a 65 px strip.

    A card whose OWN title is not in the title table (V1's `RUN CONTEXT`) adopted the
    nearest table-matching text far above it, and the band between them swallowed four
    unrelated labels — four false `out_of_card` findings. The bound is the title's own ink
    height, so it scales with the font instead of being a pixel count picked by hand.
    """
    h, w = 1000, 1400
    card_bbox = (100.0, 500.0, 300.0, 560.0)
    card_art = _FakeArtist()
    card = audit.Element(card_art, "patch", None, card_bbox, "foreground", "col")
    probe = _FakeProbe(h, w, {id(card_art): _outline_ink(h, w, card_bbox)})

    near_art, far_art = _FakeArtist(), _FakeArtist()
    near = audit.Element(near_art, "text", "SATIATION", (100.0, 562.0, 260.0, 572.0),
                         "foreground", "col")                     # one line above the card
    far = audit.Element(far_art, "text", "SATIATION", (100.0, 625.0, 260.0, 635.0),
                        "foreground", "col")                      # 65 px above the card

    assert audit._title_strips([card, far], [(far, "Satiation", False)], probe) == [], (
        "a title 65 px above a card is not that card's title; treating it as one is the "
        "bug that produced four false out_of_card findings")

    strips = audit._title_strips([card, near], [(near, "Satiation", False)], probe)
    assert len(strips) == 1
    desc, mask = strips[0]
    assert "SATIATION" in desc
    rows = np.flatnonzero(mask.any(axis=1))
    assert mask.any() and (rows.max() - rows.min() + 1) <= 4, (
        "the strip must be the thin band between the card edge and its title")


def test_owning_title_attributes_by_column_not_by_x_proximity():
    """Instrument bug 4: caption attribution used horizontal proximity.

    A vitals row prints its label hard left and its value hard right of the same panel, so
    an x-overlap test rejects the row's own title and blames the caption on whichever
    panel happens to sit at that x — turning the observed-caption rule into noise. Here
    the caption's own title does NOT overlap it in x, and a foreign-column title does.
    """
    ax_left, ax_right = _FakeAx(), _FakeAx()
    own = audit.Element(_FakeArtist(ax_left), "text", "SATIATION",
                        (185.0, 430.0, 240.0, 440.0), "foreground", "left")
    foreign = audit.Element(_FakeArtist(ax_right), "text", "COLLISION",
                            (300.0, 420.0, 400.0, 430.0), "foreground", "right")
    caption = audit.Element(_FakeArtist(ax_left), "text", "OBS:  0.13",
                            (300.0, 400.0, 360.0, 410.0), "foreground", "left")

    got = audit._owning_title(caption, [(own, "Satiation", False),
                                        (foreign, "Collision", False)])
    assert got is not None and got[1] == "Satiation", (
        "the caption belongs to the title in its OWN column, even though the foreign "
        "column's title is nearer in x and in y")


def test_paint_order_decides_the_fill_class():
    """The fill split is decided by composition order, and only within one Axes."""
    ax, other = _FakeAx(), _FakeAx()
    text = audit.Element(_FakeArtist(ax, zorder=3.0), "text", "+84", (0, 0, 10, 10),
                         "foreground", "arena")
    above = audit.Element(_FakeArtist(ax, zorder=5.0), "patch", None, (0, 0, 10, 10),
                          "foreground", "arena")
    below = audit.Element(_FakeArtist(ax, zorder=2.0), "patch", None, (0, 0, 10, 10),
                          "foreground", "arena")
    elsewhere = audit.Element(_FakeArtist(other, zorder=9.0), "patch", None, (0, 0, 10, 10),
                              "foreground", "other")

    assert audit._is_painted_over(text, above)
    assert not audit._is_painted_over(text, below)
    assert not audit._is_painted_over(text, elsewhere)

    # equal zorder falls back to insertion order, which is how matplotlib breaks the tie
    tie_ax = _FakeAx()
    first = audit.Element(_FakeArtist(tie_ax, zorder=3.0), "text", "x", (0, 0, 10, 10),
                          "foreground", "tie")
    second = audit.Element(_FakeArtist(tie_ax, zorder=3.0), "patch", None, (0, 0, 10, 10),
                           "foreground", "tie")
    assert audit._is_painted_over(first, second)
    assert not audit._is_painted_over(second, first)


# --------------------------------------------------------------- positive controls


@pytest.fixture(scope="module")
def control_results():
    if not _have("M4"):
        pytest.skip(_MISSING)
    return audit.run_controls(FIXTURES, verbose=False)


@pytest.fixture(scope="module")
def v1_m4():
    """(findings, breakdown) for the V1 campfire frame — rendered once for this module."""
    if not _have("M4"):
        pytest.skip(_MISSING)
    fi = audit.load_inputs(FIXTURES / "M4" / "M4", 0)
    findings, probe, _info = audit.audit_frame(fi, "v1")
    probe.close()
    return findings, dict(fi.breakdown)


@pytest.fixture(scope="module")
def v1_m1():
    if not _have("M1"):
        pytest.skip(_MISSING)
    fi = audit.load_inputs(FIXTURES / "M1" / "M1", 0)
    findings, probe, _info = audit.audit_frame(fi, "v1")
    probe.close()
    return findings


@pytest.mark.integration
@pytest.mark.parametrize("name", sorted(audit.CONTROLS))
def test_positive_control_fires(control_results, name):
    """Parametrised over EVERY control, so one can never be added and left untested."""
    r = control_results[name]
    assert r["fired"], (
        f"{name} ({r['what']}) was NOT flagged on {r['frame']}. The audit is not "
        f"sensitive enough to be trusted — do not weaken the defect list or lower the "
        f"threshold to make this pass."
    )


@pytest.mark.integration
@pytest.mark.parametrize("name", sorted(CONTROL_COORDS))
def test_positive_control_hits_at_the_pinned_coordinates(control_results, name):
    """The right rule on the right pair AT THE WRONG PLACE is also a miss.

    Without this, a collision that moved to a different part of the frame — a relayout
    that broke something else, or an instrument that started reporting a different
    region — would still pass every control.
    """
    hits = control_results[name]["hits"]
    for rule, a_tok, b_tok, px, bbox in CONTROL_COORDS[name]:
        matched = [h for h in hits
                   if h["rule"] == rule and a_tok in h["a"]
                   and (b_tok is None or b_tok in h["b"])]
        assert matched, f"{name}: no {rule} hit pairing {a_tok!r} with {b_tok!r}: {hits}"
        assert any(_bbox_close(h["bbox"], bbox)
                   and (px == 0 or _px_close(h["overlap_px"], px))
                   for h in matched), (
            f"{name}: {rule} fired on the right elements but not at the pinned place. "
            f"Expected bbox ~{bbox} and ~{px}px; got "
            f"{[(h['bbox'], h['overlap_px']) for h in matched]}")


@pytest.mark.integration
def test_d1_is_text_on_text_between_the_named_elements(control_results):
    hits = control_results["D1"]["hits"]
    assert any(h["rule"] == "text_over_text" and "OBS:" in h["a"]
               and "THERMOCEPTION" in h["b"] and h["overlap_px"] >= audit.MIN_OVERLAP_PX
               for h in hits), hits


@pytest.mark.integration
def test_d3_is_text_on_a_panel_border(control_results):
    hits = control_results["D3"]["hits"]
    assert any(h["rule"] == "text_over_border" and "MINIMAP" in h["a"] for h in hits), hits


@pytest.mark.integration
@pytest.mark.parametrize("name,modality", [("D8", "Interoceptive Nociception"),
                                           ("D12", "Proprioception")])
def test_panel_absent_controls_name_the_modality(control_results, name, modality):
    hits = control_results[name]["hits"]
    assert any(h["rule"] == "panel_absent" and h["a"] == modality for h in hits), hits
    assert all(h["bbox"] is None for h in hits), (
        "a dropped panel has no location in the frame; reporting one would be invented")


# ---------------------------------------------------------------- NEGATIVE controls
#
# What the audit must NOT report. These are what distinguish this instrument from one that
# flags everything — a distinction no positive control can make.


@pytest.mark.integration
def test_v1_m4_absent_panels_are_exactly_proprioception(v1_m4):
    """The EXACT absent set, not just 'Proprioception is in it'.

    Two ways this fails loudly. A panel that V1 really does draw appearing here is a bug
    in the audit's own title table, not a dropped panel — that is instrument bug 3, where
    `BODY TEMP   DIE -15 / +15` was reported as a silently dropped Body Temperature panel.
    And D8 (V2 drops interoceptive nociception) can only mean anything if V1, on the same
    world, does draw it.
    """
    findings, breakdown = v1_m4
    absent = {f.a for f in findings if f.rule == "panel_absent"}
    assert absent == {"Proprioception"}, (
        f"expected exactly one silently dropped panel on V1 M4 (D12); got {sorted(absent)}")
    for drawn in ("Body Temperature", "Interoceptive Nociception", "Thermoception"):
        assert drawn in breakdown, f"{drawn} should be in this world's breakdown"
        assert drawn not in absent, f"V1 does draw {drawn}; reporting it absent is a bug"


@pytest.mark.integration
def test_v1_m4_finding_counts_are_pinned(v1_m4):
    """Exact per-rule counts on the campfire frame, plus the rules that must stay silent."""
    findings, _breakdown = v1_m4
    counts = audit.summarise(findings)
    assert counts == V1_M4_COUNTS, (
        f"V1 M4 finding counts moved: {counts} != {V1_M4_COUNTS}. Either a frozen "
        f"renderer changed (check v1_path_guard) or the instrument did.")
    for rule in SILENT_RULES:
        if rule in V1_M4_COUNTS:
            continue
        assert counts.get(rule, 0) == 0, f"{rule} must be silent on V1 M4"


@pytest.mark.integration
def test_v1_m1_finding_counts_are_pinned(v1_m1):
    """The same, on the default world — the frame where D5 lives."""
    counts = audit.summarise(v1_m1)
    assert counts == V1_M1_COUNTS, (
        f"V1 M1 finding counts moved: {counts} != {V1_M1_COUNTS}")
    for rule in SILENT_RULES:
        assert counts.get(rule, 0) == 0, f"{rule} must be silent on V1 M1"


@pytest.mark.integration
def test_v1_m1_reproduces_d5_in_the_vitals_column(v1_m1):
    """D5: a row's OBS value colliding with the next row's REAL value, three times."""
    d5 = [f for f in v1_m1
          if f.rule == "text_over_text" and "OBS:" in f.a and "REAL:" in f.b]
    assert len(d5) == 3, d5
    for f in d5:
        assert 14 <= f.overlap_px <= 20, f
        assert f.bbox is not None and 300 <= f.bbox[0] <= 380, (
            f"D5 lives in the left vitals column, x 317-364; got {f.bbox}")


@pytest.mark.integration
def test_text_collisions_are_not_double_counted(v1_m1):
    """Instrument bug 5: a text-text collision was reported once from each side."""
    pairs = [frozenset((f.a, f.b)) for f in v1_m1 if f.rule == "text_over_text"]
    assert len(pairs) == len(set(pairs)), f"the same pair reported twice: {pairs}"


@pytest.mark.integration
def test_v1_m4_out_of_card_flags_only_the_escaped_readout(v1_m4):
    """Instrument bug 2, at frame level: the strip must not swallow unrelated labels."""
    findings, _breakdown = v1_m4
    hits = [f for f in findings if f.rule == "out_of_card"]
    assert len(hits) == 1, hits
    assert "REAL: --" in hits[0].a and "EXTERO NOCICEPTION" in hits[0].b
    for f in hits:
        for never in ("RUN CONTEXT", "MINIMAP", "10x10"):
            assert never not in f.a, (
                f"{never!r} is not in a card's title strip; flagging it is the 65 px "
                f"strip bug")


@pytest.mark.integration
def test_fill_class_splits_the_thermal_scale_label_from_the_in_widget_labels(v1_m4):
    """`text_over_fill` is NOT a uniformly benign class, and this pins which is which.

    Five of the six fill collisions on this frame are labels composed after the widget
    they sit on — legible by design. The sixth is not: the thermal scale's max-value end
    label (`+63` on the current fixture — the number is the world's hottest temperature,
    so it moves whenever the world does, while the geometry below does not)
    is anchored at axes-fraction 0.77000 while the colour strip's last segment runs to
    0.77220 (each segment is drawn 0.002 wider than its share to close the hairline gaps),
    and the segment is composed after the label, so it paints over the tip of the `+`.
    That is a real, structural, world-independent layout defect, not an artefact of how
    the rule attributes ink — see the module docstring for the two pixel-based
    discriminators that were measured and rejected before composition order was kept.
    """
    findings, _breakdown = v1_m4
    benign = {f.a for f in findings if f.rule == "text_over_fill"}
    covered = [f for f in findings if f.rule == "fill_over_text"]

    # Re-pinned 2026-09-16 for the demonstration loosening (_DEMO_LOOSENING in
    # make_render_fixture_recordings.py): every literal here is a TEMPERATURE the world
    # draws, so all of them moved, while the count (5, see V1_M4_COUNTS) and the covered
    # label's bbox and overlap below did NOT — which is what says the world changed and
    # the renderer did not. Four distinct strings for five collisions: two thermoception
    # cells read the same temperature on this frame.
    assert benign == {"text '+0.00  real +0.00'", "text '+8'", "text '-10'",
                      "text '-9'"}, sorted(benign)
    assert len(covered) == 1, covered
    f = covered[0]
    assert "'+63'" in f.a and "Rectangle" in f.b
    assert _bbox_close(f.bbox, (866, 801, 867, 804)), f.bbox
    assert _px_close(f.overlap_px, 6), f.overlap_px


@pytest.mark.integration
def test_numeric_in_arena_is_reachable_and_fires():
    """§D5.2 item 10 is wired to the CLI (`--arena-axes`) and demonstrably works.

    V1 draws its arena into an UNLABELLED Axes, so the rule cannot be pointed at V1's
    arena at all. The dormant V2 labels its axes, so the rule is exercised here against a
    real frame by naming an axes that is known to contain numeric text — which is what
    proves the rule fires, rather than merely that it runs and stays silent.
    """
    if not _have("M4"):
        pytest.skip(_MISSING)
    fi = audit.load_inputs(FIXTURES / "M4" / "M4", 0)
    findings, probe, _info = audit.audit_frame(fi, "v2", arena_axes="thermoception")
    probe.close()
    hits = [f for f in findings if f.rule == "numeric_in_arena"]
    assert len(hits) == 5, hits
    # Re-pinned 2026-09-16 for the demonstration loosening: these are the thermoception
    # readings the frame draws, so they move with the world while the hit COUNT does not.
    # Five hits, four distinct strings — two cells read the same temperature here.
    assert {"text '+56'", "text '+8'", "text '-10'", "text '-9'"} == {h.a for h in hits}

    quiet, probe2, _i = audit.audit_frame(fi, "v2", arena_axes=None)
    probe2.close()
    assert not [f for f in quiet if f.rule == "numeric_in_arena"], (
        "without --arena-axes the rule must not run: the arena cannot be guessed")


# ------------------------------------------------------------------ mutation controls


@pytest.mark.integration
def test_collision_controls_go_quiet_when_the_measurement_is_broken(monkeypatch):
    """Raise the overlap threshold out of reach: the pixel controls must stop firing.

    This is what separates a measurement from a constant. If D1/D6 still "fire" here,
    they are not being decided by measured pixels.
    """
    if not _have("M4"):
        pytest.skip(_MISSING)
    monkeypatch.setattr(audit, "MIN_OVERLAP_PX", 10 ** 9)
    fi = audit.load_inputs(FIXTURES / "M4" / "M4", 0)
    findings, probe, _info = audit.audit_frame(fi, "v1")
    probe.close()
    rules = {f.rule for f in findings}
    for pixel_rule in ("text_over_text", "text_over_border", "text_over_fill",
                       "fill_over_text", "out_of_card"):
        assert pixel_rule not in rules, f"{pixel_rule} survived an unsatisfiable threshold"
    # The breakdown-driven rule does not depend on pixel overlap, so it must SURVIVE.
    assert "panel_absent" in rules


@pytest.mark.integration
def test_an_ink_that_flags_everything_breaks_the_calibrated_counts(monkeypatch):
    """The negative-control mutation: make `ink()` claim every pixel for every element.

    Such an instrument is maximally sensitive and completely useless — and every positive
    control in this file still fires under it, because a control only asks whether a
    finding appeared. What must break is the pinned counts and the silent rules, and this
    test asserts that they do.
    """
    if not _have("M4"):
        pytest.skip(_MISSING)
    monkeypatch.setattr(audit.FrameProbe, "ink",
                        lambda self, el: np.ones((self.h, self.w), dtype=bool))
    fi = audit.load_inputs(FIXTURES / "M4" / "M4", 0)
    findings, probe, _info = audit.audit_frame(fi, "v1")
    probe.close()
    counts = audit.summarise(findings)

    assert counts != V1_M4_COUNTS, (
        "an instrument that flags every pixel produced the calibrated counts; the counts "
        "cannot then be evidence of anything")
    assert counts.get("text_over_text", 0) > V1_M4_COUNTS["text_over_text"]
    assert counts.get("clipped", 0) > 0, (
        "with all-True ink every text reaches the canvas edge; `clipped` staying silent "
        "would mean the silent rules are not measuring anything")
    assert counts.get("out_of_canvas", 0) > 0


# ==================================================== Phase 0d: the audit sees squares
#
# CP0.3b. Every control here is a FIGURE THIS FILE BUILDS: `cell_overdraw` needs its own
# axes name, and V1 draws its arena into an unlabelled Axes, so the rule cannot run on any
# frozen frame at all (§R19.4 item 6). The forms are the REAL ones from `cells.py` -- a
# control drawn with stand-in shapes would calibrate the instrument against a painter
# nobody ships.
#
# The negative controls are the half that matters. A rule that fired on everything would
# "catch" every mutation, so what separates this instrument from that one is the correct
# squares it must stay silent on, and the exact 1.000 each of them measures.
#
# WHAT CHANGED ON 2026-09-17 (plan Revision 27), because this section was built around a
# drawing that is no longer shipped. Terrain used to be a BED: a full-bleed floor covering
# the square, with the movers standing on top of it. The approved design draws a rock as a
# centred glyph, so:
#
#   * the bed forms are gone, and with them the graded "inset the bed until it stops being
#     classified as the floor" family (M-F2) that the survival floor's defect side rested
#     on. A new graded family is registered below and MEASURED, not assumed.
#   * terrain is an OCCUPANT, so `agent + rock` is now a two-kind square that must show
#     both -- the archetype this whole redesign started from, and a case the old rule
#     exempted by construction.
#   * the square is 96 px at the approved 5-wide window rather than a fixed 50, so the
#     controls run at the size the renderer actually draws.

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import (FancyBboxPatch, Polygon,  # noqa: E402
                                Rectangle)

from src.environment.dashboard import cells as C  # noqa: E402
from src.environment.dashboard import layout as L  # noqa: E402
from src.environment.dashboard import painters as PN  # noqa: E402
from src.environment.dashboard import palette as P  # noqa: E402

#: The square the renderer draws at the approved design's own window (5 wide, in a
#: fixed 480 px arena). `TIGHT` is the square at a 10-wide window, which is where the
#: artwork's floors get close -- both are exercised.
CELL = L.arena_cell_px(5)          # 96.0
TIGHT = L.arena_cell_px(10)        # 48.0
_PT = 72 / 100.0


def _coll(ax, shapes, z):
    """One compound form as ONE artist -- the §R20.8 rule the painter also obeys.

    IT CALLS THE PAINTER'S OWN FILL, and that is the point rather than a shortcut:
    a control drawn by a private copy of the draw path calibrates the instrument
    against a painter nobody ships.
    """
    form = PN._collection(ax, z)
    PN._fill(form, shapes)
    return form


def _arena_figure(squares, *, rows=1, cols=1, cell=CELL, mutation=None, cover=0.0,
                  fig_facecolor=P.FIGURE_FACECOLOR, footprint=None, action="UP"):
    """A small arena composed exactly as `painters.build_arena` composes one.

    It carries a PAGE rectangle in its own Axes like the real dashboard, so precondition
    (b') is exercised against a real second Axes instead of being assumed away.
    """
    w_px, h_px = cols * cell, rows * cell
    fig = plt.figure(figsize=((w_px + 40) / 100.0, (h_px + 40) / 100.0), dpi=100)
    fig.set_layout_engine("none")
    fig.set_facecolor(fig_facecolor)

    bg = fig.add_axes([0, 0, 1, 1], label="page")
    bg.axis("off")
    bg.add_patch(Rectangle((0, 0), 1, 1, transform=bg.transAxes, fc=P.CANVAS, lw=0,
                           zorder=0))

    ax = fig.add_axes([20 / (w_px + 40), 20 / (h_px + 40),
                       w_px / (w_px + 40), h_px / (h_px + 40)], label="arena")
    ax.set_autoscale_on(False)
    ax.axis("off")
    ax.patch.set_visible(False)
    ax.set_xlim(0, w_px)
    ax.set_ylim(h_px, 0)

    ground_z = C.TOKEN_Z + 1 if mutation == "M-G" else C.GROUND_Z

    for r in range(rows):
        for c in range(cols):
            cx, cy = (c + 0.5) * cell, (r + 0.5) * cell
            names = list(squares.get((r, c), ()))
            ax.add_patch(FancyBboxPatch(
                (cx - cell / 2 + 1, cy - cell / 2 + 1), cell - 2, cell - 2,
                boxstyle="round,pad=0,rounding_size=8", fc=P.TRACK, ec="none", lw=0,
                zorder=ground_z))
            if not names:
                continue
            drawn = C.compose(names, cx, cy, cell, action=action)
            if mutation == "M-E":
                # the original defect: every occupant on the square's own centre
                h = C.shared_h(cell)
                drawn = [(nm, C.token(nm, cx, cy, h, action=action))
                         for nm in C.by_priority(names)[:C.MAX_SLOTS]]
            if mutation == "M-T":
                # the terrain glyph drawn LAST and centred, i.e. variant H's floor
                # put back on top of the movers it used to sit under
                terrain = [n for n in names if n in C.TERRAIN_NAMES]
                assert terrain, "M-T needs a terrain in the square"
                drawn = [(nm, sh) for nm, sh in drawn if nm not in C.TERRAIN_NAMES]
                drawn.append((terrain[0],
                              C.token(terrain[0], cx, cy, C.solo_h(terrain[0], cell))))
            for i, (_nm, shapes) in enumerate(drawn):
                _coll(ax, shapes, C.TOKEN_Z + i * 0.01)
            if mutation == "M-C" and cover > 0:
                # GRADED OCCLUSION: an opaque strip laid over the FIRST token, above it,
                # covering `cover` of its height. This is what sweeps the survival floor
                # -- the token survives with FEWER PIXELS rather than vanishing, which is
                # the only condition under which the RATIO is the thing being tested.
                #
                # IT REACHES PAST THE SQUARE ON PURPOSE (`clip_on=False`), and that is
                # what makes it an OCCLUDER rather than a third occupant. The rule
                # classifies an element with ink on both sides of a square's boundary as
                # an overlay passing through -- a sense's footprint diamond is the real
                # example -- so it stays in the occluder set without being counted as
                # something standing in the square. Drawn inside the square it was
                # classified as a token, the square then held three components against
                # two kinds, and the family fired through the COMPONENT COUNT while never
                # once consulting the floor it was registered to sweep.
                sl = C.slots(names, cx, cy, cell)[0]
                hw, hh = C.fit_box(sl.name, sl.h)
                ax.add_patch(Rectangle((sl.cx - hw - 12, sl.cy - hh), 2 * hw + 24,
                                       2 * hh * cover, fc=P.TRACK, ec="none", lw=0,
                                       clip_on=False, zorder=C.TOKEN_Z + 2))
    if footprint is not None:
        fr, fc_ = footprint
        cx, cy = (fc_ + 0.5) * cell, (fr + 0.5) * cell
        ax.add_patch(Polygon([(cx, cy - cell), (cx + cell, cy), (cx, cy + cell),
                              (cx - cell, cy)], closed=True, fc="none", ec=P.IRIS,
                             lw=1.5 * _PT, zorder=C.FOOTPRINT_Z))

    fig.canvas.draw()
    frame = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    return fig, frame


def _run_cells(squares, *, rows=1, cols=1, restrict_work=True,
               floor=audit.CELL_FLOOR_FRACTION, **kw):
    fig, frame = _arena_figure(squares, rows=rows, cols=cols, **kw)
    probe = audit.FrameProbe(fig, frame)
    try:
        return audit.cell_overdraw(probe, "arena", {k: tuple(v) for k, v in
                                                    squares.items()},
                                   rows, cols, restrict_work=restrict_work,
                                   floor_fraction=floor)
    finally:
        probe.close()


# The correct squares. Each must produce ZERO findings and measure exactly 1.000.
#
# HALF OF THEM HOLD TERRAIN, which is the point: until Revision 27 a rock was "the
# floor" and was dropped from the square's kinds before the rule ever ran, so the case
# the redesign exists for was the one case it could not see.
NEGATIVE_CELLS = {
    "empty square": (dict(), {}),
    "lone agent on bare ground": (dict(), {(0, 0): ["agent"]}),
    "lone campfire": (dict(), {(0, 0): ["campfire"]}),
    "lone rock": (dict(), {(0, 0): ["rock"]}),
    "agent on a rock": (dict(), {(0, 0): ["agent", "rock"]}),
    "food on a bush": (dict(), {(0, 0): ["food", "bush"]}),
    "two movers with the agent": (dict(), {(0, 0): ["agent", "predator"]}),
    "three-way with a campfire": (dict(), {(0, 0): ["agent", "predator", "campfire"]}),
    "four-way with a tree": (
        dict(), {(0, 0): ["agent", "predator", "food", "tree"]}),
    "four movers": (
        dict(), {(0, 0): ["agent", "predator", "food", "neutral"]}),
    "footprint edge through an occupied square": (
        dict(rows=3, cols=3, footprint=(1, 1)), {(1, 1): ["agent", "predator"]}),
    "adjacent squares": (
        dict(rows=1, cols=2),
        {(0, 0): ["agent", "predator"], (0, 1): ["food", "neutral"]}),
    "at a ten-wide window": (dict(cell=TIGHT), {(0, 0): ["agent", "rock"]}),
    "four-way at a ten-wide window": (
        dict(cell=TIGHT), {(0, 0): ["agent", "predator", "food", "tree"]}),
}


@pytest.mark.parametrize("name", sorted(NEGATIVE_CELLS))
def test_cell_overdraw_is_silent_on_every_negative_control(name):
    """A correct square produces NOTHING. This is the half a mutation cannot measure."""
    kw, squares = NEGATIVE_CELLS[name]
    findings, _measured = _run_cells(squares, **kw)
    assert findings == [], (
        f"{name}: a CORRECT square produced {len(findings)} finding(s): "
        f"{[(f.rule, f.detail) for f in findings]}. Do not loosen a constant to silence "
        f"this -- a false alarm here means the classifier is wrong, and the forbidden fix "
        f"is to stop counting something as able to occlude (§R20's narrowing rule).")


def test_correct_shared_squares_measure_exactly_one_point_zero():
    """§R19.1 step 5: a correct composition measures 1.000, not 'about 1'."""
    for name in ("agent on a rock", "two movers with the agent",
                 "four-way with a tree", "adjacent squares",
                 "four-way at a ten-wide window"):
        kw, squares = NEGATIVE_CELLS[name]
        _f, measured = _run_cells(squares, **kw)
        assert measured, f"{name} measured nothing at all"
        for m in measured:
            assert m["survival"], f"{name} measured no survival ratio"
            for s in m["survival"]:
                assert s == 1.0, f"{name}: survival {s} is below 1.000"


def test_the_floor_classifier_separates_the_ground_from_the_occupants():
    """Pin the two populations `CELL_FLOOR_FRACTION` has to separate.

    The rule tells a square's FLOOR from the things standing on it by measured ink
    area. Under variant H the two populations were "largest correct token" against
    "smallest bed"; with terrain drawn as a glyph there is no bed, and the thing the
    floor test now identifies is the square's own GROUND FILL. Both sides are
    measured here rather than argued, exactly as §R21.2 required of the old pair.
    """
    def _fractions(squares, **kw):
        fig, frame = _arena_figure(squares, **kw)
        probe = audit.FrameProbe(fig, frame)
        try:
            ax = audit._named_axes(fig, "arena")
            rect = audit.square_rects(ax, 1, 1)[(0, 0)]
            square = audit._rect_mask(probe.h, probe.w, *rect)
            area = float(square.sum())
            out = {}
            for e in probe.elements:
                if e.axes_name != "arena":
                    continue
                out.setdefault(e.kind, []).append(
                    int((probe.ink(e) & square).sum()) / area)
            return out
        finally:
            probe.close()

    lone = _fractions({(0, 0): ["agent"]})
    token = max(lone.get("image", [0]))
    ground = max(lone.get("patch", [0]))
    assert token < audit.CELL_FLOOR_FRACTION < ground, (
        f"the floor {audit.CELL_FLOOR_FRACTION} does not separate the two populations "
        f"it exists to separate: largest correct token {token:.4f}, ground {ground:.4f}. "
        f"Below the token the classifier calls an OCCUPANT the floor (the square then "
        f"reports no one standing in it); above the ground it calls the FLOOR an "
        f"occupant. The response is to move the constant IN THE PLAN with both numbers.")
    # The largest correct token is the LONE AGENT, whose translucent halo is ink and
    # whose solo size the approved design sets at 0.396 x cell. These two numbers are
    # what moved the constant from 0.48 to 0.74 (see the audit's own comment): the
    # upper population used to be a terrain BED at 0.5168, and with terrain drawn as a
    # glyph the only thing above the tokens is the ground fill.
    assert token == pytest.approx(0.5013, abs=0.01), token
    assert ground == pytest.approx(0.9366, abs=0.01), ground


# The mutations CP0.3b gates on, each with the rule that must catch it.
MUTATION_CELLS = {
    # every occupant drawn on the square's own centre -- the original defect
    "M-E": (dict(mutation="M-E"), {(0, 0): ["agent", "predator"]}, "cell_overdraw"),
    # the terrain glyph drawn last and centred: variant H's floor put back ON TOP
    "M-T": (dict(mutation="M-T"), {(0, 0): ["agent", "rock"]}, "cell_overdraw"),
    "M-T at a ten-wide window": (dict(mutation="M-T", cell=TIGHT),
                                 {(0, 0): ["agent", "bush"]}, "cell_overdraw"),
    # the ground fill drawn ABOVE the tokens, on a figure background it cannot be
    # told apart from -- the occluder the probe cannot see
    "M-G": (dict(mutation="M-G", fig_facecolor=P.CANVAS),
            {(0, 0): ["agent", "predator"]}, "cell_probe_blind"),
    # graded occlusion: the survival floor's own family (below)
    "M-C@0.06": (dict(mutation="M-C", cover=0.06),
                 {(0, 0): ["agent", "predator"]}, "cell_overdraw"),
    "M-C@0.12": (dict(mutation="M-C", cover=0.12),
                 {(0, 0): ["agent", "predator"]}, "cell_overdraw"),
    "M-C@0.25": (dict(mutation="M-C", cover=0.25),
                 {(0, 0): ["agent", "predator"]}, "cell_overdraw"),
}

#: The members the gap table's DEFECT side is made of. All three must fire the survival
#: floor specifically -- a member caught by another rule has survival 1.0 and would make
#: the margin look wider than it is (§R20.3 *Fails if:*).
COVER_FAMILY = ("M-C@0.06", "M-C@0.12", "M-C@0.25")


@pytest.mark.parametrize("name", sorted(MUTATION_CELLS))
def test_cell_overdraw_fires_on_every_mutation(name):
    kw, squares, rule = MUTATION_CELLS[name]
    findings, _measured = _run_cells(squares, **kw)
    assert findings, (
        f"{name} PASSED the audit. The instrument is not sensitive enough to be trusted; "
        f"do not weaken the mutation to make this green.")
    assert any(f.rule == rule for f in findings), (
        f"{name} fired, but not via {rule!r}: {sorted({f.rule for f in findings})}. A "
        f"control that fires for the wrong reason counts as not firing.")


def test_a_pure_isolated_ink_rule_would_pass_the_occlusion_mutation():
    """The demonstration that measuring SURVIVING ink was needed at all (§R19.1).

    The covering strip is drawn AFTER the token, so the token keeps every pixel of its
    own isolated ink: an isolated-ink component count sees two whole occupants and a
    perfectly good square. Only the ink that SURVIVES the painting order can tell that a
    quarter of one of them is not on screen.

    M-C rather than M-T is the mutation used here, and the difference is the point: a
    terrain glyph dropped on top of a mover makes their inks TOUCH, so the component
    count catches that one on its own. A thin covering strip does not, which is exactly
    the blind spot the survival floor exists to cover.
    """
    findings, measured = _run_cells({(0, 0): ["agent", "predator"]},
                                    mutation="M-C", cover=0.25)
    m = measured[0]
    assert m["components_isolated"] == m["n_kinds"] == 2, (
        f"the isolated-ink count must still look CORRECT here, or this mutation is not "
        f"demonstrating the blind spot it was written for: {m}")
    assert min(m["survival"]) < audit.SURVIVAL_MIN, m
    assert any("keeps only" in f.detail for f in findings), findings


def test_terrain_dropped_on_a_mover_is_caught_by_the_component_count():
    """M-T: variant H's floor put back ON TOP of the occupants it used to sit under.

    This is the defect the reversal could plausibly reintroduce -- a terrain glyph drawn
    last and centred -- so it is registered as its own control. It is caught by a
    different half of the rule than the strip above, and the test says which, because
    "it fired" without "through what" is how a control quietly stops measuring.
    """
    kw, squares, _rule = MUTATION_CELLS["M-T"]
    findings, measured = _run_cells(squares, **kw)
    m = measured[0]
    assert m["n_kinds"] == 2, m
    assert m["components_visible"] < m["n_kinds"] or m["components_isolated"] < m["n_kinds"], (
        f"a terrain glyph drawn over a mover left both of them looking present: {m}")
    assert any(f.rule == "cell_overdraw" for f in findings), findings


def test_the_survival_floor_sits_in_a_gap_and_not_on_a_cliff():
    """§R20.3's gap table, re-measured for the drawing that is actually shipped.

    One side is the minimum over the correct controls, the other the maximum over the
    graded cover family. The family is NEW -- the old one shrank a terrain BED until it
    stopped being classified as the floor, and there is no bed any more -- so the numbers
    are measured here rather than carried over.

    IF THIS GAP EVER COLLAPSES the answer is to report it in the plan with both
    populations and, if they overlap, to state a detection limit -- never to nudge the
    constant until today's frames pass.
    """
    correct = []
    for name in ("lone agent on bare ground", "agent on a rock", "food on a bush",
                 "two movers with the agent", "three-way with a campfire",
                 "four-way with a tree", "adjacent squares",
                 "footprint edge through an occupied square"):
        kw, squares = NEGATIVE_CELLS[name]
        _f, measured = _run_cells(squares, **kw)
        correct += [s for m in measured for s in m["survival"]]

    defect, fired = [], 0
    for name in COVER_FAMILY:
        kw, squares, _rule = MUTATION_CELLS[name]
        findings, measured = _run_cells(squares, **kw)
        if any("keeps only" in f.detail for f in findings):
            fired += 1
            # EACH MEMBER CONTRIBUTES ITS OWN WORST RATIO, not every ratio below 1.0
            # that happens to be in the square. The covering strip grazes the SECOND
            # token's edge by a pixel or two, so collecting everything under 1.0 put a
            # 0.9982 into the defect population and made the gap look collapsed when
            # the real defects measured 0.75 and below. The statistic the gap table
            # needs is the shallowest defect that FIRES, which is the worst ratio of
            # each member.
            defect.append(min(s for m in measured for s in m["survival"]))

    assert fired == len(COVER_FAMILY), (
        f"only {fired} of {len(COVER_FAMILY)} cover members fired the SURVIVAL FLOOR. A "
        f"member caught by another rule has survival 1.0 and never measured this floor, "
        f"so the table would rest on fewer members than it claims. Report that -- do not "
        f"move a cover fraction to make the count come out")
    assert len(defect) >= len(COVER_FAMILY)

    lo, hi = min(correct), max(defect)
    assert lo == 1.0, f"the correct side is not 1.000: {sorted(set(correct))}"
    assert hi < audit.SURVIVAL_MIN <= lo, (
        f"SURVIVAL_MIN={audit.SURVIVAL_MIN} does not sit in the measured gap "
        f"({hi:.4f}, {lo:.4f}]")
    # the shallowest member must still be a REAL defect rather than a rounding error
    assert 0.5 < hi < audit.SURVIVAL_MIN, hi


def test_cross_axes_composition_order_agrees_with_the_pixels():
    """§R20.1: the figure-wide rank is PINNED by a render, not trusted.

    `_is_painted_over` refuses to order two Axes, so `L(p)` needs a rank across the whole
    figure. A derived order the pixels contradict is a broken instrument, and this is the
    cheapest possible place to find that out -- so the control renders both orders and
    asks the composite what actually won.
    """
    for z_a, z_b in ((1.0, 2.0), (2.0, 1.0)):
        fig = plt.figure(figsize=(0.6, 0.6), dpi=100)
        fig.set_facecolor("#FFFFFF")
        red, blue = "#E03151", "#5B4BDB"
        ax_a = fig.add_axes([0, 0, 1, 1], label="A", zorder=z_a)
        ax_b = fig.add_axes([0, 0, 1, 1], label="B", zorder=z_b)
        for ax, colour in ((ax_a, red), (ax_b, blue)):
            ax.axis("off")
            ax.patch.set_visible(False)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.add_patch(Rectangle((0.2, 0.2), 0.6, 0.6, fc=colour, lw=0))
        fig.canvas.draw()
        img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()

        order = audit.DrawOrder(fig)
        pa = [c for c in ax_a.get_children() if isinstance(c, Rectangle)][0]
        pb = [c for c in ax_b.get_children() if isinstance(c, Rectangle)][0]
        last = pa if order.of(pa) > order.of(pb) else pb
        expect = red if last is pa else blue
        from matplotlib.colors import to_rgb
        want = np.asarray([round(v * 255) for v in to_rgb(expect)])
        got = img[30, 30].astype(int)
        assert np.abs(got - want).max() <= 2, (
            f"zorders ({z_a}, {z_b}): the comparator says {expect} is composed last, but "
            f"the pixel is {got}. The derived draw order contradicts the render.")
        plt.close(fig)


def test_probing_only_what_can_reach_a_square_changes_no_finding():
    """§R20.7 item 4: the ONLY permitted exclusion is from the work, never the occluders.

    An element whose padded bbox cannot meet a square cannot put ink in it, so skipping it
    must be undetectable in the output. Asserted by running one control both ways.
    """
    kw, squares = NEGATIVE_CELLS["footprint edge through an occupied square"]
    fast, m_fast = _run_cells(squares, restrict_work=True, **kw)
    full, m_full = _run_cells(squares, restrict_work=False, **kw)
    assert [f.as_dict() for f in fast] == [f.as_dict() for f in full]
    assert m_fast == m_full


@pytest.mark.parametrize("cell", [CELL, TIGHT])
def test_adjacent_slot_tokens_share_zero_pixels(cell):
    """§R19.4 item 2, re-measured at the sizes the renderer now draws.

    If this ever reads non-zero the fix is the SLOT GEOMETRY -- `SHARED_FRAC` against the
    quarter-square a slot occupies -- and never a loosened tolerance.
    """
    fig, frame = _arena_figure({(0, 0): ["agent", "predator"]}, cell=cell)
    probe = audit.FrameProbe(fig, frame)
    try:
        toks = [e for e in probe.elements
                if e.axes_name == "arena" and e.kind == "image"]
        assert len(toks) == 2
        shared = int((probe.ink(toks[0]) & probe.ink(toks[1])).sum())
        assert shared == 0, (
            f"two adjacent-slot tokens share {shared}px at a {cell:.0f}px square")
    finally:
        probe.close()


def test_an_outline_shaped_token_part_fails_rather_than_leaving_the_count():
    """§R20.7 item 1's failing-direction guard.

    An element whose ink sits on the perimeter of its own bbox is normally a square
    outline or a seam and is excluded. A RING-SHAPED TOKEN PART drawn as its own artist is
    that same shape, and must not be able to vanish from the count.
    """
    from matplotlib.patches import Circle

    fig, frame = _arena_figure({(0, 0): ["agent"]})
    ax = audit._named_axes(fig, "arena")
    ax.add_patch(Circle((CELL / 2, CELL / 2), 15, fc="none", ec=P.NOCI, lw=2 * _PT,
                        zorder=C.TOKEN_Z + 2))
    fig.canvas.draw()
    frame = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    probe = audit.FrameProbe(fig, frame)
    try:
        findings, _m = audit.cell_overdraw(probe, "arena", {(0, 0): ("agent",)}, 1, 1)
    finally:
        probe.close()
    assert any(f.rule == "outline_like_token" for f in findings), (
        f"a ring-shaped part left the token count silently: "
        f"{sorted({f.rule for f in findings})}")


def test_every_artist_of_a_square_is_enumerated():
    """Regression: every Collection used to drop out of the element list.

    `Collection.get_window_extent` reports an EMPTY bbox, which the enumerator filtered
    out -- and an artist that is not an Element is never hidden by `FrameProbe._draw`, so
    it was drawn into every isolated render and ate the ink of whatever it covered.

    Since Revision 27 every entity in a square is the user's artwork, so a square holding
    a bush and an agent carries TWO images and no collection at all. Both must be
    enumerated and both must measure ink.
    """
    fig, frame = _arena_figure({(0, 0): ["bush", "agent"]})
    probe = audit.FrameProbe(fig, frame)
    try:
        arena = [e for e in probe.elements if e.axes_name == "arena"]
        images = [e for e in arena if e.kind == "image"]
        assert len(images) == 2, f"expected the agent and the bush: {images}"
        for e in images:
            assert probe.ink(e).any(), f"{e.label} enumerated but measures no ink"
        # ... and the page rectangle underneath must measure its FULL ink, because the
        # tokens are hidden during its isolated render.
        page = [e for e in probe.elements if e.axes_name == "page" and e.kind == "patch"]
        assert page and int(probe.ink(page[0]).sum()) == probe.h * probe.w, (
            "the page rectangle's isolated ink is short, so something that is not an "
            "Element is still being painted over it")
    finally:
        probe.close()


def test_terrain_counts_as_an_occupant_now():
    """The reversal of variant H, asserted on the INSTRUMENT rather than the painter.

    `cell_overdraw` used to filter terrain out of a square's kinds before measuring
    anything, so a square holding a rock and an agent was a ONE-kind square and the rock
    could not be reported missing however it was drawn. It is two kinds now.
    """
    _f, measured = _run_cells({(0, 0): ["agent", "rock"]})
    assert measured[0]["n_kinds"] == 2
    assert sorted(measured[0]["kinds"]) == ["agent", "rock"]
    assert not hasattr(audit, "TERRAIN_KINDS"), (
        "the audit still carries the terrain exemption it was supposed to lose")
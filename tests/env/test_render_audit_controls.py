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
# frozen frame at all (§R19.4 item 6). The forms are the REAL ones from `cells.py` — a
# control drawn with stand-in shapes would calibrate the instrument against a painter
# nobody ships.
#
# The negative controls are the half that matters. A rule that fired on everything would
# "catch" all five mutations, so what separates this instrument from that one is the nine
# correct squares it must stay silent on, and the exact 1.000 each of them measures.

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PatchCollection  # noqa: E402
from matplotlib.patches import (FancyBboxPatch, Polygon,  # noqa: E402
                                Rectangle, Wedge)

from src.environment.dashboard import cells as C  # noqa: E402
from src.environment.dashboard import palette as P  # noqa: E402

CELL = 50.0
_PT = 72 / 100.0


def _coll(ax, shapes, z):
    """One compound form as ONE artist — the §R20.8 rule the painter also obeys."""
    coll = PatchCollection([s.patch for s in shapes], match_original=False, zorder=z)
    coll.set_facecolor([s.fc for s in shapes])
    coll.set_edgecolor([s.ec for s in shapes])
    coll.set_linewidth([s.lw * _PT for s in shapes])
    ax.add_collection(coll)
    coll.set_transform(ax.transData)
    return coll


def _arena_figure(squares, *, rows=1, cols=1, mutation=None, inset=0.0,
                  fig_facecolor=P.FIGURE_FACECOLOR, footprint=None, action="UP"):
    """A small arena composed exactly as `painters.build_arena` composes one.

    It carries a PAGE rectangle in its own Axes like the real dashboard, so precondition
    (b′) is exercised against a real second Axes instead of being assumed away.
    """
    w_px, h_px = cols * CELL, rows * CELL
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

    ground_z = C.TOKEN_Z + 1 if mutation == "M-F1g" else C.GROUND_Z
    bed_z = C.TOKEN_Z + 1 if mutation in ("M-F1", "M-F2") else C.BED_Z

    for r in range(rows):
        for c in range(cols):
            cx, cy = (c + 0.5) * CELL, (r + 0.5) * CELL
            names = list(squares.get((r, c), ()))
            ax.add_patch(FancyBboxPatch(
                (cx - CELL / 2 + 1, cy - CELL / 2 + 1), CELL - 2, CELL - 2,
                boxstyle="round,pad=0,rounding_size=8", fc=P.TRACK, ec="none", lw=0,
                zorder=ground_z))
            terrain = [n for n in names if n in C.TERRAIN_NAMES]
            rest = [n for n in names if n not in C.TERRAIN_NAMES]
            if terrain:
                size = CELL * (1 - 2 * inset) if mutation == "M-F2" else CELL
                _coll(ax, C.bed(terrain[0], cx, cy, size), bed_z)
            if rest:
                _bed, drawn = C.compose(names, cx, cy, CELL, action=action)
                if mutation == "M-E":
                    h = C.slot_h(len(rest), CELL)
                    drawn = [(nm, C.token(nm, cx, cy, h, action=action, shared=True))
                             for nm in C.by_priority(rest)]
                for i, (_nm, shapes) in enumerate(drawn):
                    _coll(ax, shapes, C.TOKEN_Z + i * 0.01)
            if "agent" in rest:
                ax.add_patch(FancyBboxPatch(
                    (cx - CELL / 2 + 2, cy - CELL / 2 + 2), CELL - 4, CELL - 4,
                    boxstyle="round,pad=0,rounding_size=7", fc="none", ec=P.IRIS,
                    lw=2 * _PT, zorder=C.OUTLINE_Z))
    if footprint is not None:
        fr, fc_ = footprint
        cx, cy = (fc_ + 0.5) * CELL, (fr + 0.5) * CELL
        ax.add_patch(Polygon([(cx, cy - CELL), (cx + CELL, cy), (cx, cy + CELL),
                              (cx - CELL, cy)], closed=True, fc="none", ec=P.IRIS,
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


# The nine correct squares. Each must produce ZERO findings and measure exactly 1.000.
NEGATIVE_CELLS = {
    "empty square": (dict(), {}),
    "campfire bed + one token": (dict(), {(0, 0): ["campfire", "neutral"]}),
    "bush bed + agent": (dict(), {(0, 0): ["bush", "agent"]}),
    "two movers with the agent": (dict(), {(0, 0): ["agent", "predator"]}),
    "three-way with the agent": (dict(), {(0, 0): ["agent", "predator", "food"]}),
    "four-way with the agent": (
        dict(), {(0, 0): ["agent", "predator", "food", "neutral"]}),
    "footprint edge through an occupied square": (
        dict(rows=3, cols=3, footprint=(1, 1)), {(1, 1): ["agent", "predator"]}),
    "adjacent slots at 50px": (
        dict(rows=1, cols=2),
        {(0, 0): ["agent", "predator"], (0, 1): ["food", "neutral"]}),
}


@pytest.mark.parametrize("name", sorted(NEGATIVE_CELLS))
def test_cell_overdraw_is_silent_on_every_negative_control(name):
    """A correct square produces NOTHING. This is the half a mutation cannot measure."""
    kw, squares = NEGATIVE_CELLS[name]
    findings, _measured = _run_cells(squares, **kw)
    assert findings == [], (
        f"{name}: a CORRECT square produced {len(findings)} finding(s): "
        f"{[(f.rule, f.detail) for f in findings]}. Do not loosen a constant to silence "
        f"this — a false alarm here means the classifier is wrong, and the forbidden fix "
        f"is to stop counting something as able to occlude (§R20's narrowing rule).")


@pytest.mark.xfail(strict=True, reason=(
    "MEASURED PLAN DEFECT, decision belongs to senior-developer. A lone agent on bare "
    "ground keeps its halo (1.32x its own radius), and that token's ink measures 43.76% "
    "of its square — above §R19.1 step 2's 40% 'this element IS the floor' line — so a "
    "CORRECT occupant is excluded as scenery and the square reports 0 components against "
    "1 kind. Measured populations: largest correct token 0.4376, smallest bed 0.5168, "
    "bed floor by construction 0.5184 (pinned in test_dashboard_cells.py). A floor of "
    "0.48 sits 53.5% of the way up that gap and makes this control pass. The constant is "
    "NOT moved here: §R20.3's discipline is that a constant moves in the plan text with "
    "its evidence, never in a test to turn a checkpoint green."))
def test_a_lone_agent_on_bare_ground_is_not_scenery():
    findings, _m = _run_cells({(0, 0): ["agent"]})
    assert findings == [], [(f.rule, f.detail) for f in findings]


def test_the_lone_agent_collision_is_a_constant_choice_and_both_sides_are_measured():
    """Pin the two populations the floor constant has to separate.

    The xfail above says a correct lone agent is misclassified; this says WHY, in numbers,
    so the decision to move the constant is made against measurement rather than argument.
    """
    def _largest_collection_fraction(squares):
        fig, frame = _arena_figure(squares)
        probe = audit.FrameProbe(fig, frame)
        try:
            ax = audit._named_axes(fig, "arena")
            rect = audit.square_rects(ax, 1, 1)[(0, 0)]
            square = audit._rect_mask(probe.h, probe.w, *rect)
            area = float(square.sum())
            return max(int((probe.ink(e) & square).sum()) / area
                       for e in probe.elements
                       if e.axes_name == "arena" and e.kind == "collection")
        finally:
            probe.close()

    token = _largest_collection_fraction({(0, 0): ["agent"]})
    bed = min(_largest_collection_fraction({(0, 0): [t, "neutral"]})
              for t in ("rock", "bush", "tree", "campfire"))
    assert token == pytest.approx(0.4376, abs=0.005), token
    assert bed == pytest.approx(0.5168, abs=0.005), bed
    assert token > audit.CELL_FLOOR_FRACTION, (
        "the shipped floor no longer misclassifies a lone agent — if the constant has "
        "been moved in the plan, remove the xfail above rather than this assertion")
    assert bed >= C.bed_plate_fraction(CELL) - 0.005, (
        "a bed must stay at or above its constructed plate fraction, which is what makes "
        "the bed side of this gap a pinned number rather than a measurement that drifts")


# The five mutations CP0.3b gates on, each with the rule that must catch it.
MUTATION_CELLS = {
    "M-E": (dict(mutation="M-E"), {(0, 0): ["agent", "predator"]}, "cell_overdraw"),
    "M-F1": (dict(mutation="M-F1"), {(0, 0): ["bush", "agent"]}, "cell_overdraw"),
    "M-F1g": (dict(mutation="M-F1g", fig_facecolor=P.CANVAS),
              {(0, 0): ["agent", "predator"]}, "cell_probe_blind"),
    "M-F2@0.02": (dict(mutation="M-F2", inset=0.02),
                  {(0, 0): ["bush", "agent", "predator"]}, "cell_overdraw"),
    "M-F2@0.05": (dict(mutation="M-F2", inset=0.05),
                  {(0, 0): ["bush", "agent", "predator"]}, "cell_overdraw"),
    "M-F2@0.10": (dict(mutation="M-F2", inset=0.10),
                  {(0, 0): ["bush", "agent", "predator"]}, "cell_overdraw"),
}


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


def test_a_pure_isolated_ink_rule_would_pass_the_occlusion_mutations():
    """M-F1 is the demonstration that Revision 19 was needed at all.

    The bed is drawn AFTER the token, so the token keeps every pixel of its isolated ink
    and an isolated-ink component count sees a perfectly good square. Only the surviving
    ink and the floor can tell that the viewer is looking at a bed.
    """
    kw, squares, _rule = MUTATION_CELLS["M-F1"]
    findings, measured = _run_cells(squares, **kw)
    m = measured[0]
    assert m["components_isolated"] == m["n_kinds"] == 1, (
        "the isolated-ink count must still look CORRECT here, or this mutation is not "
        "demonstrating the blind spot it was written for")
    assert m["components_visible"] == 0
    assert m["survival"] == [0.0]
    assert any("keeps only" in f.detail for f in findings)


def test_correct_shared_squares_measure_exactly_one_point_zero():
    """§R19.1 step 5: a correct composition measures 1.000, not 'about 1'.

    Includes the four-way WITH the agent — §R20.2's tightest case, where the square
    outline's inner fringe sits 0.1-1.1px from a token edge. It measures 1.000 because
    `cells.py` pins the outline BELOW the tokens; drawn above, this is what would fire.
    """
    for name in ("bush bed + agent", "two movers with the agent",
                 "four-way with the agent", "adjacent slots at 50px"):
        kw, squares = NEGATIVE_CELLS[name]
        _f, measured = _run_cells(squares, **kw)
        for m in measured:
            assert m["survival"], f"{name} measured no survival ratio at all"
            for s in m["survival"]:
                assert s == 1.0, f"{name}: survival {s} is below 1.000 — §R20.3 requires "
        assert measured


def test_the_survival_floor_sits_in_a_gap_and_not_on_a_cliff():
    """§R20.3's pre-registered gap table, asserted.

    One side is the minimum over the correct controls, the other the maximum over the
    M-F2 family. A member whose bed has been inset under the floor test is EXCLUDED from
    that maximum with its reason: it stops being a bed, is read as a token, overlaps its
    neighbour and is caught by the disjointness rule instead — still a failure, but its
    survival ratio is 1.0 and it never measured the floor.
    """
    correct = []
    for name in ("bush bed + agent", "two movers with the agent",
                 "three-way with the agent", "four-way with the agent",
                 "campfire bed + one token", "adjacent slots at 50px",
                 "footprint edge through an occupied square"):
        kw, squares = NEGATIVE_CELLS[name]
        _f, measured = _run_cells(squares, **kw)
        correct += [s for m in measured for s in m["survival"]]

    defect = []
    for name in ("M-F2@0.02", "M-F2@0.05", "M-F2@0.10"):
        kw, squares, _rule = MUTATION_CELLS[name]
        findings, measured = _run_cells(squares, **kw)
        if any("keeps only" in f.detail for f in findings):
            defect += [s for m in measured for s in m["survival"]]

    lo, hi = min(correct), max(defect)
    assert lo == 1.0, f"the correct side is not 1.000: {sorted(set(correct))}"
    assert hi < 0.5, f"the M-F2 family did not drive survival well below the floor: {hi}"
    assert hi < audit.SURVIVAL_MIN <= lo, (
        f"SURVIVAL_MIN={audit.SURVIVAL_MIN} does not sit in the measured gap "
        f"({hi:.4f}, {lo:.4f}]")
    assert lo - hi > 0.5, (
        f"the gap collapsed to {lo - hi:.4f}; the floor would then be a cliff, and the "
        f"honest response is to report that, never to move the constant to open it")


def test_cross_axes_composition_order_agrees_with_the_pixels():
    """§R20.1: the figure-wide rank is PINNED by a render, not trusted.

    `_is_painted_over` refuses to order two Axes, so `L(p)` needs a rank across the whole
    figure. A derived order the pixels contradict is a broken instrument, and this is the
    cheapest possible place to find that out — so the control renders both orders and
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


def test_adjacent_slot_tokens_share_zero_pixels_at_fifty_px():
    """§R19.4 item 2: the 0px figure came from a 40px mock; pin it at the real 50px.

    If this ever reads non-zero the fix is the KEYLINE GEOMETRY — inset the stroke so its
    outer edge lies at h — and never a loosened tolerance.
    """
    fig, frame = _arena_figure({(0, 0): ["agent", "predator"]})
    probe = audit.FrameProbe(fig, frame)
    try:
        toks = [e for e in probe.elements
                if e.axes_name == "arena" and e.kind == "collection"]
        assert len(toks) == 2
        shared = int((probe.ink(toks[0]) & probe.ink(toks[1])).sum())
        assert shared == 0, (
            f"two adjacent-slot tokens share {shared}px at a 50px square")
    finally:
        probe.close()


def test_an_outline_shaped_token_part_fails_rather_than_leaving_the_count():
    """§R20.7 item 1's failing-direction guard.

    An element whose ink sits on the perimeter of its own bbox is normally a square
    outline or a seam and is excluded. A RING-SHAPED TOKEN PART drawn as its own artist is
    that same shape, and must not be able to vanish from the count — so an outline whose
    bbox spans under 80% of the square is reported instead of excluded.
    """
    fig, frame = _arena_figure({(0, 0): ["agent"]})
    ax = audit._named_axes(fig, "arena")
    from matplotlib.patches import Circle
    ax.add_patch(Circle((25, 25), 8, fc="none", ec=P.NOCI, lw=2 * _PT,
                        zorder=C.TOKEN_Z + 2))
    fig.canvas.draw()
    frame = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    probe = audit.FrameProbe(fig, frame)
    try:
        findings, _m = audit.cell_overdraw(probe, "arena", {(0, 0): ("agent",)}, 1, 1)
    finally:
        probe.close()
    assert any(f.rule == "outline_like_token" for f in findings), (
        f"a ring-shaped part spanning ~32% of the square left the token count silently: "
        f"{sorted({f.rule for f in findings})}")


def test_collection_artists_are_enumerated_at_all():
    """Regression: every Collection used to drop out of the element list.

    `Collection.get_window_extent` reports an EMPTY bbox, which the enumerator filtered
    out — and an artist that is not an Element is never hidden by `FrameProbe._draw`, so
    it was drawn into every isolated render and ate the ink of whatever it covered. The
    redesign draws every bed and token as one PatchCollection, so without this the
    co-occupancy rule measures an arena with nothing standing in it.
    """
    fig, frame = _arena_figure({(0, 0): ["bush", "agent"]})
    probe = audit.FrameProbe(fig, frame)
    try:
        colls = [e for e in probe.elements if e.kind == "collection"]
        assert len(colls) == 2, f"expected the bed and the token: {colls}"
        for e in colls:
            assert probe.ink(e).any(), f"{e.label} enumerated but measures no ink"
        # ... and the page rectangle underneath must now measure its FULL ink, because
        # the tokens are hidden during its isolated render.
        page = [e for e in probe.elements if e.axes_name == "page" and e.kind == "patch"]
        assert page and int(probe.ink(page[0]).sum()) == probe.h * probe.w, (
            "the page rectangle's isolated ink is short, so something that is not an "
            "Element is still being painted over it")
    finally:
        probe.close()


# ------------------------------------------------------------------- the World map
def _minimap_figure(occupants, *, mutation=None, caption=True):
    """A one-square World map with the real palette colours and the real encoding."""
    fig = plt.figure(figsize=(1.2, 1.6), dpi=100)
    fig.set_layout_engine("none")
    fig.set_facecolor(P.FIGURE_FACECOLOR)
    ax = fig.add_axes([0.1, 0.4, 0.8, 0.5], label="minimap")
    ax.axis("off")
    ax.patch.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(1, 0)
    ax.add_patch(Rectangle((0, 0), 1, 1, fc=P.TRACK, lw=0, zorder=1))

    order = C.by_priority([n for n in occupants if n not in C.TERRAIN_NAMES])
    if len(order) == 1:
        from matplotlib.patches import Circle
        ax.add_patch(Circle((0.5, 0.5), 0.30, fc=P.MINIMAP_COLOUR[order[0]],
                            ec=P.WHITE, lw=1.2 * _PT, zorder=6))
    else:
        for i, nm in enumerate(order[:2]):
            ax.add_patch(Wedge((0.5, 0.5), 0.30, 90 + i * 180, 90 + (i + 1) * 180,
                               fc=P.MINIMAP_COLOUR[nm], ec=P.WHITE, lw=0.8 * _PT,
                               zorder=6 + i * 0.1))
        if mutation == "M-F3":
            from matplotlib.patches import Circle
            ax.add_patch(Circle((0.5, 0.5), 0.30, fc=P.MINIMAP_COLOUR["agent"],
                                ec=P.WHITE, lw=1.2 * _PT, zorder=9))
    if caption:
        cap = fig.add_axes([0.05, 0.05, 0.9, 0.25], label="caption")
        cap.axis("off")
        cap.text(0, 0.5, "Shared squares: two occupants split the dot", fontsize=5)
    fig.canvas.draw()
    frame = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    return fig, frame


def _run_minimap(occupants, **kw):
    fig, frame = _minimap_figure(occupants, **kw)
    probe = audit.FrameProbe(fig, frame)
    try:
        return audit.minimap_overdraw(probe, "minimap", {(0, 0): tuple(occupants)}, 1, 1)
    finally:
        probe.close()


def test_minimap_is_silent_on_a_correct_split_dot():
    assert _run_minimap(["agent", "neutral"]) == []


def test_minimap_m_f3_catches_a_dot_painted_over_the_split_wedge():
    """M-F3: the agent's dot above the split wedge.

    Measured on the COMPOSITE, because isolation would report the covered wedge as
    perfectly correct — which is the exact defect §R17.4 exists to prevent.
    """
    findings = _run_minimap(["agent", "neutral"], mutation="M-F3")
    assert any(f.rule == "minimap_overdraw" for f in findings), findings


def test_minimap_ground_truth_is_kinds_not_movers():
    """§R20.4: two predators are two movers but ONE kind and one colour.

    The withdrawn "at least as many colours as movers" wording reported a defect on this
    correct square.
    """
    assert _run_minimap(["predator", "predator"]) == []


def test_minimap_requires_the_shared_square_caption():
    findings = _run_minimap(["agent", "neutral"], caption=False)
    assert any(f.rule == "minimap_caption" for f in findings), findings


def test_the_audits_minimap_palette_matches_the_package():
    """The audit carries a COPY of the colour table, and a copy can drift.

    The audit may not import the package it audits, so the table is duplicated — and this
    test, which may import both, is what stops the duplicate becoming a different design.
    """
    assert audit.MINIMAP_PALETTE == P.MINIMAP_COLOUR
    assert set(audit.TERRAIN_KINDS) == set(C.TERRAIN_NAMES)

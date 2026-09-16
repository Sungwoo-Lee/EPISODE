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
import sys
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
    """§D5.2: the audit must not import the thing it audits."""
    leaked = [m for m in sys.modules if "environment.dashboard" in m]
    assert leaked == [], f"audit pulled in the renderer package under test: {leaked}"
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

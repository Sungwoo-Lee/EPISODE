"""figguards.py — the figure guards, shared by every study that draws through house.py.

WHY THESE EXIST, AND WHY THEY ARE GLOBAL RATHER THAN TARGETED. Each of these was added after a
defect shipped, and the first three versions were each defeated by the fix for the previous one:
wrapping tick labels to cure their collision pushed the axis label into the legend; moving two
annotations out of the data left them printed over each other; and a tick guard that tolerated
touching boxes passed two labels that read as one word. Every guard had been verified against the
rule it was fixing and against nothing else. `assert_no_text_overlap` is the total check that
replaces that pattern: text over text is always a defect, so the honest test is all text against
all text.

They live here rather than in `house.py` because house.save() is on the golden-gated path for
fifteen sensor-ladder figures; adding a stricter assertion there would fail those figures on their
next run, which is correct behaviour but not a change to make in the middle of someone else's study.
"""
import itertools

COLUMN_PX = 688


def assert_min_text_px(fig, column_px=COLUMN_PX, floor_px=9.0):
    """Assert the figure's SMALLEST DRAWN TEXT clears the legibility floor at the real column.

    `house.check_floor` computes one number from the house constant FS_LABEL at a default column of
    730px. That is not the same question: an annotation set at 8.5pt is not FS_LABEL, and this page's
    column is 688px. On the first build of this page that gap let annotations ship at 6.8px and tick
    labels at 6.1px under a build line that read "smallest label 9.3px" -- the check ran, printed a
    passing number, and measured something no reader ever sees. So this walks every visible Text
    artist and takes the true minimum. Proposed for the format register as F63.
    """
    import matplotlib.text
    w_px = fig.get_size_inches()[0] * fig.dpi
    smallest, who = None, None
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not (t.get_text() or "").strip():
            continue
        pt = t.get_fontsize()
        if smallest is None or pt < smallest:
            smallest, who = pt, (t.get_text() or "")[:40].replace("\n", " ")
    px = smallest * (fig.dpi / 72.0) * (column_px / w_px)
    if px < floor_px:
        raise SystemExit(
            f"smallest DRAWN text renders at {px:.1f}px in a {column_px}px column "
            f"(floor {floor_px}px): {smallest:g}pt on {who!r}. Raise the size or narrow the canvas; "
            f"do not lower the floor.")
    return px


def assert_ticks_dont_collide(ax, axis="x"):
    """Assert an axis's tick labels do not overprint one another.

    `house.assert_labels_fit` guards the axis label and title; `assert_text_inside_axes` guards
    hand-placed text. Neither looks at tick labels, so long categorical names silently run into each
    other -- which is what happened to the arm names on the results figure. Proposed as a second
    amendment to register F18.
    """
    fig = ax.get_figure()
    fig.canvas.draw()
    labs = ax.get_xticklabels() if axis == "x" else ax.get_yticklabels()
    boxes = [(l, l.get_window_extent()) for l in labs if (l.get_text() or "").strip()]
    for i in range(len(boxes) - 1):
        (la, a), (lb, b) = boxes[i], boxes[i + 1]
        # A HALF-PIXEL TOLERANCE IS NOT A GAP. The first version accepted boxes that merely
        # touched, and passed two three-line labels whose words ended up 5px apart on a 2175px
        # canvas -- 1.6px at the page's column, which reads as one word
        # ("neuromodulatedneuromodulated"). The gap has to be in em, not px.
        need = 0.5 * la.get_fontsize() * fig.dpi / 72.0
        gap = (b.x0 - a.x1) if axis == "x" else (b.y0 - a.y1)
        if gap < need:
            raise SystemExit(
                f"{axis}-tick labels are {gap:.1f}px apart, under the {need:.1f}px (0.5em) floor: "
                f"{la.get_text()!r} beside {lb.get_text()!r}. Wrap, shorten or rotate them.")


def assert_no_text_overlap(fig, min_gap_px=1.0):
    """Assert no drawn text overlaps any other drawn text, anywhere in the figure.

    THE REASON THIS IS ONE GLOBAL CHECK RATHER THAN SEVERAL TARGETED ONES. Every targeted guard so
    far has been defeated by the fix for the previous one. Wrapping tick labels onto three lines
    cured their collision and pushed the axis label down into the legend's band. Moving two
    annotations out of the data cured them being printed through by a line and left them printed
    through by each other. The label-fit guard checks a label against its panel, the tick guard
    checks ticks against each other, and nothing checked the whole stack -- so each fix was verified
    against the rule it was fixing and against nothing else.

    Text over text is always a defect, so the honest check is the total one: take every visible Text
    artist the figure will draw, including legend entries, and require their rendered boxes to be
    pairwise disjoint.
    """
    import itertools
    import matplotlib.text
    fig.canvas.draw()

    # Matplotlib keeps a Text artist for ticks OUTSIDE the current view; they are positioned beyond
    # the panel and are never drawn, but findobj still returns them. On a two-panel figure the left
    # panel's out-of-view tick sits under the right panel's, which is a collision no reader can see.
    # They are excluded by asking each axis which tick locations are actually in view.
    dead = set()
    for ax_ in fig.axes:
        for axis, lim in ((ax_.xaxis, ax_.get_xlim()), (ax_.yaxis, ax_.get_ylim())):
            lo, hi = sorted(lim)
            for loc, lab in zip(axis.get_ticklocs(), axis.get_ticklabels()):
                if not (lo <= loc <= hi):
                    dead.add(id(lab))

    items = []
    for t in fig.findobj(matplotlib.text.Text):
        txt = (t.get_text() or "").strip()
        if not t.get_visible() or not txt or id(t) in dead:
            continue
        try:
            bb = t.get_window_extent()
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        items.append((txt, bb))
    for (ta, a), (tb, b) in itertools.combinations(items, 2):
        ox = min(a.x1, b.x1) - max(a.x0, b.x0)
        oy = min(a.y1, b.y1) - max(a.y0, b.y0)
        if ox > min_gap_px and oy > min_gap_px:
            raise SystemExit(
                f"text is printed over text ({ox:.0f}x{oy:.0f}px overlap):\n"
                f"   {ta[:60]!r}\n   {tb[:60]!r}\n"
                f"Move one of them; a raster is a single box to the page's layout checker, so "
                f"nothing downstream can see this.")
    return len(items)


def legend_below(ax, ncol=2, offset=-0.13):
    """House legend, but with the vertical offset under the caller's control.

    `house.legend_below` hardcodes -0.13, which is tuned for one-line tick labels. Wrapping tick
    labels onto three lines to cure a collision pushes the axis label down into that fixed band, so
    the legend ends up printed over the axis label -- the fix for one guard defeating another. The
    offset belongs to the figure that knows how tall its tick labels are.
    """
    import house as _h
    leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, offset), ncol=ncol, frameon=False)
    for t in leg.get_texts():
        t.set_color(_h.INK)
        t.set_fontsize(_h.FS_LABEL)
    return leg

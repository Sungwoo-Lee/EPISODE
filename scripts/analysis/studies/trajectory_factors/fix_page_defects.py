#!/usr/bin/env python3
"""fix_page_defects.py - targeted corrections to the a01 page's pre-existing prose and legends.

The other three scripts in this folder each own a block they generate. This one owns small,
surgical fixes to text that was already on the page before any of them ran - the kind a reader
turns up by going through the figures one at a time.

Every correction is a (before, after) pair with its own assert, so a fix whose anchor has moved is
a hard failure rather than a silent no-op. That failure mode is not hypothetical: a `.replace` with
a stale anchor and no assert has silently done nothing twice in this page's history, once leaving
raw `__PC_HI__` placeholders in published text.

Idempotent by construction - a correction whose "after" is already present is skipped, so the
script can be re-run after the page is regenerated from the other three.
"""
from __future__ import annotations
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
os.chdir(ROOT)
PAGE = "docs/experiments/active/trajectory_factors/a01_hiding_drivers.html"


FIXES = [
    # ---------------------------------------------------------------------------------------
    # Figure 9 drew THREE fills and legended two. Its second bar is `aim ? --false : --true`,
    # so the two rows where the rabbit is not nearby render teal and only the aimed row renders
    # red - and a reader sees an unexplained teal. Teal and red are the SAME quantity; red is
    # emphasis on the row the finding is about, which the legend now says.
    ("figure 9 legend: the unlabelled teal",
     '''  <div class="key">
    <span><i class="sw" style="background:var(--muted);opacity:.55"></i>rabbit smells rabbit-like</span>
    <span><i class="sw" style="background:var(--false)"></i>rabbit smells predator-like</span>
  </div>''',
     '''  <div class="key">
    <span><i class="sw" style="background:var(--muted);opacity:.55"></i>rabbit smells rabbit-like</span>
    <span><i class="sw" style="background:var(--true);opacity:.75"></i>rabbit smells predator-like</span>
    <span><i class="sw" style="background:var(--false)"></i>the same, in the row this figure is about &mdash; that rabbit nearby</span>
  </div>'''),
]


def main():
    write = "--write" in sys.argv
    html = open(PAGE, encoding="utf-8").read()
    applied = skipped = 0
    for name, before, after in FIXES:
        if after in html:
            print(f"  already applied: {name}")
            skipped += 1
            continue
        if html.count(before) != 1:
            raise SystemExit(
                f"fix_page_defects: anchor for {name!r} matched {html.count(before)} times, "
                f"expected exactly 1. The page changed under this fix - re-derive it rather "
                f"than letting the replacement silently do nothing.")
        html = html.replace(before, after)
        print(f"  applied: {name}")
        applied += 1
    print(f"  {applied} applied, {skipped} already present")
    if not write:
        print("  DRY RUN - pass --write to apply")
        return
    open(PAGE, "w", encoding="utf-8").write(html)
    print(f"  wrote {PAGE}")


if __name__ == "__main__":
    main()

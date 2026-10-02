"""Drive an artifact page in a real browser and report which INTERACTIONS are broken.

WHY THIS EXISTS. `check_artifact_layout.py` renders a page and measures geometry, but it never clicks
anything, and Chrome's headless CLI floors the viewport at 500px. So the parts of a page a reader
operates - tabs, collapsed panels, the full-size figure viewer, keyboard focus - were only ever
tested by whichever review improvised a driver that day. Twice on 2026-09-14 the format reviewer
hand-built one to open a figure viewer and click tabs. This script makes that a fixed, repeatable
step, and it runs at a TRUE 390px phone viewport.

It is run-agnostic: it knows nothing about any one page, and discovers what to exercise from ARIA
roles and standard elements.

For each viewport width it reports:
  * fonts that failed to load (document.fonts entries with status "error")
  * console errors, uncaught page errors, failed requests, and requests to hosts outside the
    Artifact CSP allowlist (they would be blocked silently once published)
  * elements carrying `hidden` that still render (an author display rule beat it - register F14)
  * horizontal page overflow at that true width
  * tabs ([role=tablist]): each tab clicked shows exactly its own panel; ArrowRight moves selection
  * <details>: each one opens when its summary is clicked
  * figure viewer: each `figure img[role=button]` opens a visible [role=dialog] on Enter, Escape
    closes it, and focus returns to the figure
  * focus walk: every Tab stop (up to --max-tabs) shows a visible focus indicator
and writes a screenshot per width plus one per tab panel and per opened viewer.

Usage
-----
    python scripts/claude/check_artifact_interactions.py <page.html> [--out DIR] [--widths 390 834 1440]

Exit 0 when nothing is broken, 1 otherwise. Needs the `playwright` Python package; it drives the
system Chrome (/usr/bin/google-chrome), so no browser download is required.
"""
from __future__ import annotations
import argparse, json, os, sys, tempfile
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_artifact_layout import HOST_SKELETON_HEAD  # same skeleton the Artifact host injects

from playwright.sync_api import sync_playwright

CHROME = "/usr/bin/google-chrome"
# Hosts the Artifact CSP admits (Artifact tool description). data:, blob: and file: are local.
ALLOWED_HOSTS = {"cdnjs.cloudflare.com", "cdn.jsdelivr.net", "cdn.tailwindcss.com", "code.jquery.com",
                 "fonts.googleapis.com", "fonts.gstatic.com"}

FOCUS_PROBE = """() => {
  const el = document.activeElement;
  if (!el || el === document.body) return null;
  const cs = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  const ring = (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== 'none';
  return {tag: el.tagName.toLowerCase(), id: el.id || '', cls: (el.className && el.className.baseVal === undefined) ? String(el.className).slice(0, 40) : '',
          text: (el.getAttribute('aria-label') || el.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 50),
          ring, w: Math.round(r.width), h: Math.round(r.height)};
}"""


def wrap(src: str) -> str:
    body = open(src, encoding="utf-8").read()
    return HOST_SKELETON_HEAD + body + "</body></html>"


def check_width(browser, html_path: str, width: int, out: str, max_tabs: int) -> dict:
    rep = {"width": width, "broken": [], "notes": []}
    bad = rep["broken"].append
    ctx = browser.new_context(viewport={"width": width, "height": 900}, device_scale_factor=1)
    page = ctx.new_page()
    page.on("console", lambda m: m.type == "error" and bad(f"console error: {m.text[:160]}"))
    page.on("pageerror", lambda e: bad(f"uncaught script error: {str(e)[:160]}"))
    page.on("requestfailed", lambda r: bad(f"request failed: {r.url[:120]} ({r.failure})"))

    def on_request(r):
        u = urlparse(r.url)
        if u.scheme in ("http", "https") and u.hostname not in ALLOWED_HOSTS:
            bad(f"request to a host the Artifact CSP blocks: {u.hostname}")
    page.on("request", on_request)

    page.goto("file://" + html_path, wait_until="load")
    page.evaluate("document.fonts.ready.then(() => true)")
    page.wait_for_timeout(300)

    for f in page.evaluate("""() => [...document.fonts].filter(f => f.status === 'error')
                               .map(f => f.family + ' ' + f.weight)"""):
        bad(f"font failed to load: {f}")

    for h in page.evaluate("""() => [...document.querySelectorAll('[hidden]')]
        .filter(e => getComputedStyle(e).display !== 'none')
        .map(e => e.tagName.toLowerCase() + (e.id ? '#' + e.id : ''))"""):
        bad(f"element marked hidden still renders (F14): {h}")

    ov = page.evaluate("() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]")
    if ov[0] > ov[1] + 1:
        bad(f"page scrolls sideways: content {ov[0]}px in a {ov[1]}px viewport")

    page.screenshot(path=f"{out}/page_{width}.png", full_page=True)

    # --- tabs ---------------------------------------------------------------------------------
    lists = page.locator('[role="tablist"]')
    for li in range(lists.count()):
        tabs = lists.nth(li).locator('[role="tab"]')
        n = tabs.count()
        for ti in range(n):
            tab = tabs.nth(ti)
            name = tab.inner_text().strip()[:30]
            tab.click()
            state = page.evaluate("""(el) => {
                const all = [...el.closest('[role=tablist]').querySelectorAll('[role=tab]')];
                return all.map(t => {
                  const p = document.getElementById(t.getAttribute('aria-controls'));
                  return {sel: t.getAttribute('aria-selected'),
                          shown: !!p && getComputedStyle(p).display !== 'none' && p.getBoundingClientRect().height > 0};
                });
            }""", tab.element_handle())
            for k, s in enumerate(state):
                want = (k == ti)
                if (s["sel"] == "true") != want or s["shown"] != want:
                    bad(f"tablist {li + 1}: after clicking '{name}', tab {k + 1} selected={s['sel']} panel shown={s['shown']}")
            panel_id = tab.get_attribute("aria-controls")
            if panel_id:
                p = page.locator(f"#{panel_id}")
                if p.is_visible():
                    p.screenshot(path=f"{out}/tab{li + 1}_{ti + 1}_{width}.png")
        if n > 1:
            tabs.nth(0).click()
            tabs.nth(0).focus()
            page.keyboard.press("ArrowRight")
            if tabs.nth(1).get_attribute("aria-selected") != "true":
                bad(f"tablist {li + 1}: ArrowRight does not move the selection")
            tabs.nth(0).click()

    # --- details ------------------------------------------------------------------------------
    dets = page.locator("details")
    for di in range(dets.count()):
        d = dets.nth(di)
        if d.get_attribute("open") is None:
            summ = d.locator("summary").first
            if summ.count():
                summ.click()
                if d.get_attribute("open") is None:
                    bad(f"details {di + 1}: clicking its summary does not open it")
                summ.click()

    # --- figure viewer --------------------------------------------------------------------------
    figs = page.locator('figure img[role="button"]')
    rep["notes"].append(f"{figs.count()} clickable figure(s), {lists.count()} tablist(s), {dets.count()} details")
    for fi in range(figs.count()):
        img = figs.nth(fi)
        img.scroll_into_view_if_needed()
        img.focus()
        page.keyboard.press("Enter")
        page.wait_for_timeout(250)
        dlg = page.locator('[role="dialog"]:visible')
        if dlg.count() == 0:
            bad(f"figure {fi + 1}: Enter does not open a visible full-size viewer")
            continue
        page.screenshot(path=f"{out}/viewer{fi + 1}_{width}.png")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        if page.locator('[role="dialog"]:visible').count():
            bad(f"figure {fi + 1}: Escape does not close the viewer")
        elif not page.evaluate("(el) => document.activeElement === el", img.element_handle()):
            bad(f"figure {fi + 1}: focus does not return to the figure after closing")

    # --- focus walk -----------------------------------------------------------------------------
    # Give the document keyboard focus first: a headless page that was never clicked has none, and
    # the first Tab then goes nowhere. Walk until focus comes back to a stop already seen.
    page.evaluate("() => { window.scrollTo(0, 0); if (document.activeElement) document.activeElement.blur(); }")
    page.mouse.click(1, 1)
    seen, keys, no_ring, empties = 0, set(), [], 0
    for _ in range(max_tabs):
        page.keyboard.press("Tab")
        info = page.evaluate(FOCUS_PROBE)
        if info is None:
            empties += 1
            if empties > 2:
                break
            continue
        key = (info["tag"], info["id"], info["text"], info["w"], info["h"])
        if key in keys:
            break
        keys.add(key)
        seen += 1
        rep.setdefault("tab_stops", []).append(f"{info['tag']}{'#' + info['id'] if info['id'] else ''} '{info['text']}'")
        if not info["ring"]:
            no_ring.append(f"{info['tag']}{'#' + info['id'] if info['id'] else ''} '{info['text']}'")
    rep["notes"].append(f"{seen} tab stop(s) walked" + (" (limit reached)" if seen >= max_tabs else ""))
    if seen == 0:
        bad("focus walk reached no element - nothing on the page takes keyboard focus, or the walk failed")
    for s in sorted(set(no_ring)):
        bad(f"keyboard focus not visible on: {s}")

    ctx.close()
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("--out", default="tmp/artifact_interactions")
    ap.add_argument("--widths", nargs="+", type=int, default=[390, 834, 1440])
    ap.add_argument("--max-tabs", type=int, default=60)
    a = ap.parse_args()

    src = os.path.abspath(a.page)
    os.makedirs(a.out, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
        tf.write(wrap(src))
        wrapped = tf.name

    reports, total = [], 0
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True, args=["--no-sandbox"])
        try:
            for w in a.widths:
                r = check_width(browser, wrapped, w, a.out, a.max_tabs)
                reports.append(r)
                total += len(r["broken"])
                print("=" * 74)
                print(f"viewport {w}px   ({'; '.join(r['notes'])})")
                print("=" * 74)
                for b in r["broken"] or ["nothing broken"]:
                    print("  " + b)
                print(f"  screenshots: {a.out}/*_{w}.png")
        finally:
            browser.close()
            os.unlink(wrapped)

    with open(f"{a.out}/interactions.json", "w") as fh:
        json.dump(reports, fh, indent=2)
    print("=" * 74)
    print(f"{total} problem(s) across {len(a.widths)} viewport(s); report {a.out}/interactions.json")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()

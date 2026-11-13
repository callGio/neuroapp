#!/usr/bin/env python3
"""Playwright checks for viewer/public/imaging.html.

Usage: python3 scripts/tests/test_imaging.py [--port 8765]

Serves viewer/public with python3 -m http.server, then runs the page in system Chrome
at 1280x800 and 390x844, with and without reduced motion. Screenshots go to
/home/claude/stage/shots6/. Prints PASS/FAIL per check and a summary; exit 1 on failure.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "viewer" / "public"
SHOTS = Path("/home/claude/stage/shots6")
METHODS = ["mri", "dti", "ct", "fmri", "pet", "eeg", "meg"]

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f"  ({detail})" if detail and not cond else ""))


def serve(port):
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                            cwd=PUBLIC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/imaging.html", timeout=1)
            return proc
        except Exception:
            time.sleep(0.1)
    proc.kill()
    raise SystemExit("server did not start")


def run_case(browser, base, w, h, reduced, tag):
    ctx = browser.new_context(viewport={"width": w, "height": h},
                              reduced_motion="reduce" if reduced else "no-preference",
                              device_scale_factor=1, has_touch=w < 760)
    page = ctx.new_page()
    errors, failed, foreign = [], [], []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("requestfailed", lambda r: failed.append(r.url))
    page.on("response", lambda r: failed.append(f"{r.status} {r.url}") if r.status >= 400 else None)

    def on_request(r):
        if not r.url.startswith(base) and not r.url.startswith("data:") and not r.url.startswith("blob:"):
            foreign.append(r.url)
    page.on("request", on_request)

    page.goto(base + "/imaging.html")
    page.wait_for_selector("body[data-ready='1']", timeout=10000)
    page.wait_for_timeout(300)
    p = f"[{tag}] "

    check(p + "content loaded", page.locator("#load-err").is_hidden())
    check(p + "header has three mode links, Imaging current",
          page.locator(".modes a").count() == 3 and page.locator(".modes a[aria-current='page']").inner_text() == "Imaging")
    check(p + "seven method chips", page.locator("#chips .chip").count() == 7)
    check(p + "two families", page.locator("#fam .card").count() == 2)

    # no horizontal overflow
    ov = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check(p + "no horizontal overflow", ov <= 1, f"overflow {ov}px")

    page.screenshot(path=str(SHOTS / f"imaging_{tag}_top.png"))

    # chart: bars and picker
    bars = page.locator("#chart .bar")
    check(p + "chart has 5 drawn bars (activity methods + DTI)", bars.count() == 5, str(bars.count()))
    ok_all = True
    for m in METHODS:
        page.locator(f"#picker button[data-method='{m}']").click()
        txt = page.locator("#res-detail").inner_text()
        name = page.evaluate(f"document.querySelector('#chips .chip[data-method={m}]').textContent")
        if name.strip() not in txt:
            ok_all = False
    check(p + "every method selectable from picker", ok_all)
    page.locator("#chart .bar[data-method='fmri']").click()
    check(p + "chart bar click selects", "fMRI" in page.locator("#res-detail").inner_text())
    page.locator("#chart .bar[data-method='eeg']").focus()
    page.keyboard.press("Enter")
    check(p + "chart bar keyboard select", "EEG" in page.locator("#res-detail").inner_text())
    check(p + "table has 7 rows", page.locator("#res-table tbody tr").count() == 7)
    page.locator("#tradeoff").scroll_into_view_if_needed()
    page.locator("#tradeoff").screenshot(path=str(SHOTS / f"imaging_{tag}_chart.png"))

    # level switch
    page.locator(".seg button[data-level='beginner']").click()
    intro_b = page.locator("#intro").inner_text()
    sum_b = page.locator("#m-fmri .summary").inner_text()
    page.locator(".seg button[data-level='expert']").click()
    intro_e = page.locator("#intro").inner_text()
    sum_e = page.locator("#m-fmri .summary").inner_text()
    check(p + "level switch changes text", intro_b != intro_e and sum_b != sum_e)
    stored = page.evaluate("JSON.parse(localStorage.getItem('neuroapp.profile.v1')||'{}').level")
    check(p + "level stored under viewer key", stored == "expert", str(stored))
    check(p + "expert shows caveat", page.locator("#m-fmri .caveat").count() == 1)
    page.reload()
    page.wait_for_selector("body[data-ready='1']")
    check(p + "level persists after reload",
          page.locator(".seg button[data-level='expert']").get_attribute("aria-pressed") == "true")
    page.locator(".seg button[data-level='beginner']").click()

    # method cards reachable (and openable on phones)
    all_cards = True
    for m in METHODS:
        page.locator(f"#chips .chip[data-method='{m}']").click()
        page.wait_for_timeout(50)
        if not page.locator(f"#mb-{m}").is_visible():
            all_cards = False
    check(p + "every method card reachable and visible", all_cards)
    if w < 760:
        t = page.locator("#m-pet .mtoggle")
        t.click()
        hidden = not page.locator("#mb-pet").is_visible()
        t.click()
        check(p + "card toggle collapses and expands", hidden and page.locator("#mb-pet").is_visible())
    page.locator("#m-fmri").screenshot(path=str(SHOTS / f"imaging_{tag}_card_fmri.png"))
    page.locator("#m-meg").screenshot(path=str(SHOTS / f"imaging_{tag}_card_meg.png"))

    # citations
    cite = page.locator("#m-fmri .cite").first
    cite.click()
    pop = page.locator("#cite-pop")
    link = pop.locator("a")
    check(p + "cite popover opens with safe link",
          pop.is_visible() and link.count() == 1 and link.get_attribute("rel") == "noopener noreferrer")
    page.keyboard.press("Escape")
    check(p + "cite popover closes with Escape", pop.is_hidden())

    # EEG explorer
    els = page.locator("#head-box .el")
    check(p + "21 electrodes", els.count() == 21, str(els.count()))
    page.locator("#head-box .el[data-el='F3']").click()
    d = page.locator("#el-detail").inner_text()
    check(p + "electrode decoded (F3)", "frontal" in d and "left" in d, d)
    page.locator("#head-box .el[data-el='Pz']").click()
    check(p + "electrode decoded (Pz)", "midline" in page.locator("#el-detail").inner_text())
    sizes = page.evaluate("[...document.querySelectorAll('#head-box .el')].map(b=>{const r=b.getBoundingClientRect();return Math.min(r.width,r.height)})")
    check(p + "electrode targets >= 44px", min(sizes) >= 44, str(min(sizes)))
    texts = set()
    for b in ["delta", "theta", "alpha", "beta", "gamma"]:
        page.locator(f"#bands button[data-band='{b}']").click()
        texts.add(page.locator("#band-text").inner_text())
    check(p + "five bands give five texts", len(texts) == 5)
    play = page.locator("#wave-play").inner_text()
    if reduced:
        check(p + "reduced motion: wave not autoplaying", play == "Play", play)
        a = page.evaluate("document.getElementById('wave').toDataURL()")
        page.wait_for_timeout(400)
        b2 = page.evaluate("document.getElementById('wave').toDataURL()")
        check(p + "reduced motion: static trace", a == b2)
    else:
        check(p + "wave animates by default", play == "Pause", play)
    page.locator("#eeg").screenshot(path=str(SHOTS / f"imaging_{tag}_eeg.png"))

    # quiz
    n = page.evaluate("fetch('./content/imaging.json').then(r=>r.json()).then(d=>d.chooser.length)")
    fb_ok = True
    for i in range(n):
        page.locator("#quiz-opts button").first.click()
        if not page.locator("#quiz-fb .verdict").inner_text().strip():
            fb_ok = False
        if i == 0:
            page.locator("#quiz").screenshot(path=str(SHOTS / f"imaging_{tag}_quiz.png"))
        page.locator("#quiz-next").click()
    check(p + "quiz answers give feedback", fb_ok)
    check(p + "quiz feedback is aria-live", page.locator("#quiz-fb").get_attribute("aria-live") == "polite")
    check(p + "quiz shows score", "of " + str(n) in page.locator("#quiz-q").inner_text())
    page.locator("#quiz-opts button", has_text="Try again").click()
    check(p + "quiz try again", "Question 1 of" in page.locator("#quiz-progress").inner_text())

    # glossary and sources
    check(p + "glossary rendered", page.locator("#gloss > div").count() >= 8)
    nsrc = page.evaluate("fetch('./content/imaging.json').then(r=>r.json()).then(d=>Object.keys(d.sources).length)")
    check(p + "every source listed", page.locator("#src-list li").count() == nsrc)
    page.locator("#foot-src-btn").click()
    check(p + "footer sources control", page.locator("#foot-src-list li").count() == nsrc
          and page.locator("#foot-sources").is_visible())
    ext = page.evaluate("[...document.querySelectorAll('a[target=_blank]')].every(a=>a.rel==='noopener noreferrer')")
    check(p + "external links rel=noopener noreferrer", ext)

    # keyboard focus visible on a chip
    page.evaluate("document.activeElement && document.activeElement.blur(); window.scrollTo(0,0)")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
    check(p + "visible focus ring", outline not in ("none", ""), outline)

    page.screenshot(path=str(SHOTS / f"imaging_{tag}_full.png"), full_page=True)
    check(p + "no console errors", not errors, "; ".join(errors[:3]))
    check(p + "no failed requests", not failed, "; ".join(failed[:3]))
    check(p + "no requests to other hosts", not foreign, "; ".join(foreign[:3]))
    ctx.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    SHOTS.mkdir(parents=True, exist_ok=True)
    rc = subprocess.call([sys.executable, str(Path(__file__).with_name("validate_content.py")),
                          str(PUBLIC / "content" / "imaging.json")])
    check("content JSON validates", rc == 0)
    proc = serve(args.port)
    base = f"http://127.0.0.1:{args.port}"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path="/usr/bin/google-chrome",
                                         args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
            for w, h in ((1280, 800), (390, 844)):
                for reduced in (False, True):
                    run_case(browser, base, w, h, reduced, f"{w}x{h}{'_rm' if reduced else ''}")
            browser.close()
    finally:
        proc.terminate()
    passed = sum(1 for r in results if r[1])
    print(f"\n{passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

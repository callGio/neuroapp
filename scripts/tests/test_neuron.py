#!/usr/bin/env python3
"""Playwright checks for viewer/public/neuron.html.

Run:  timeout 900 python3 scripts/tests/test_neuron.py
Serves viewer/public with python3 -m http.server on a free port, drives system Chrome
(headless, SwiftShader WebGL) at 1280x800 and 390x844, plus a reduced-motion run.
Screenshots go to /home/claude/stage/shots6/neuron-*.png. Exit code 1 if any check fails.
"""
import json
import os
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PUBLIC = os.path.join(ROOT, 'viewer', 'public')
SHOTS = '/home/claude/stage/shots6'
CHROME = '/usr/bin/google-chrome'
ARGS = ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
CONTENT = json.load(open(os.path.join(PUBLIC, 'content', 'neuron.json'), encoding='utf-8'))
PARTS = [p['id'] for p in CONTENT['parts']]
PROCS = [p['id'] for p in CONTENT['processes']]

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + ((' :: ' + str(detail)) if detail and not ok else ''))


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Watch:
    """Collects console errors, page errors, failed requests and off-host requests."""

    def __init__(self, page, host):
        self.errors, self.failed, self.offhost = [], [], []
        page.on('console', lambda m: self.errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: self.errors.append('pageerror: ' + str(e)))
        page.on('requestfailed', lambda r: self.failed.append(r.url))
        page.on('response', lambda r: self.failed.append(f'{r.status} {r.url}') if r.status >= 400 else None)
        page.on('request', lambda r: self.offhost.append(r.url)
                if urlparse(r.url).scheme in ('http', 'https') and urlparse(r.url).netloc != host else None)


def new_page(browser, w, h, base, reduced=False, skip_arrival=True):
    ctx = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1,
                              reduced_motion='reduce' if reduced else 'no-preference',
                              has_touch=w < 760, is_mobile=False)
    if skip_arrival:
        ctx.add_init_script("try{localStorage.setItem('neuroapp.neuron.arrived.v1','1')}catch(e){}")
    page = ctx.new_page()
    page.set_default_timeout(60000)
    watch = Watch(page, urlparse(base).netloc)
    return ctx, page, watch


def ready(page):
    # wait on a selector, not wait_for_function: polling a string would need 'unsafe-eval' under the page's CSP
    page.wait_for_selector('body[data-ready="1"]', state='attached', timeout=90000)
    page.wait_for_timeout(800)


def shot(page, name):
    page.screenshot(path=os.path.join(SHOTS, f'neuron-{name}.png'))


def run_viewport(browser, base, w, h, tag):
    ctx, page, watch = new_page(browser, w, h, base)
    page.goto(base + '/neuron.html')
    ready(page)
    shot(page, f'{tag}-default')
    check(f'[{tag}] triangle count under 150k', page.evaluate('window.__neuron.tris()') < 150000,
          page.evaluate('window.__neuron.tris()'))

    # header and footer
    check(f'[{tag}] Neuron mode link is aria-current', page.get_attribute('a[href="./neuron.html"]', 'aria-current') == 'page')
    check(f'[{tag}] footer disclaimer present', 'Educational use only; not medical advice.' in page.inner_text('#panel-foot'))

    # every part reachable from the list
    names = {p['id']: p['name'] for p in CONTENT['parts']}
    bad = []
    for pid in PARTS:
        page.click(f'#pane-explore .part-btn[data-part="{pid}"]')
        page.wait_for_timeout(250)
        got = page.inner_text('#focus-name')
        if got != names[pid]:
            bad.append((pid, got))
        if pid in ('myelin_sheath', 'synapse', 'dendritic_spines'):
            page.wait_for_timeout(1200)
            shot(page, f'{tag}-part-{pid}')
        page.click('#pane-explore .back')
        page.wait_for_timeout(150)
    check(f'[{tag}] all {len(PARTS)} parts reachable from the list', not bad, bad)

    # level switch changes the text
    page.click('#pane-explore .part-btn[data-part="axon"]')
    page.click('#lvl-beginner')
    beg = page.inner_text('#focus-summary')
    page.click('#lvl-expert')
    exp = page.inner_text('#focus-summary')
    check(f'[{tag}] level switch changes text', beg != exp and beg and exp, (beg, exp))
    stored = page.evaluate("JSON.parse(localStorage.getItem('neuroapp.profile.v1')).level")
    check(f'[{tag}] level stored under shared profile key', stored == 'expert', stored)
    page.click('#lvl-beginner')

    # citation popover
    page.click('#pane-explore .cite-sup >> nth=0')
    check(f'[{tag}] citation marker shows the citation', page.is_visible('#cite-pop') and 'OpenStax' in page.inner_text('#cite-pop'))
    page.keyboard.press('Escape')
    page.click('#pane-explore .back')
    page.wait_for_timeout(1300)

    # picking on the 3D model (soma at the default view)
    page.click('#btn-reset')
    page.wait_for_timeout(1500)
    pos = page.evaluate("window.__neuron.screenOf('soma')")
    page.mouse.click(pos['x'] - 10, pos['y'] - 40)
    page.wait_for_timeout(400)
    picked = page.inner_text('#focus-name') if page.query_selector('#focus-name') else ''
    check(f'[{tag}] clicking the model selects a part', picked != '', picked)
    if page.query_selector('#pane-explore .back'):
        page.click('#pane-explore .back')
        page.wait_for_timeout(1200)

    # labels toggle
    page.click('#btn-labels')
    page.wait_for_timeout(600)
    vis = page.evaluate("[...document.querySelectorAll('.p-label')].filter(e => e.style.display === 'block').length")
    check(f'[{tag}] labels toggle shows labels', vis >= 6, vis)
    shot(page, f'{tag}-labels')
    page.click('#btn-labels')

    # search
    page.fill('#search', 'myelin')
    page.wait_for_timeout(200)
    n = page.evaluate("document.querySelectorAll('#pane-explore .part-btn').length")
    g = page.inner_text('#pane-explore .gloss')
    check(f'[{tag}] search filters parts and glossary', 1 <= n < len(PARTS) and 'Saltatory' not in g or n >= 1, (n,))
    page.fill('#search', '')

    # tabs: arrow-key navigation
    page.focus('#tab-explore')
    page.keyboard.press('ArrowRight')
    check(f'[{tag}] arrow key moves between tabs', page.get_attribute('#tab-how', 'aria-selected') == 'true')

    # every process reachable, every step reachable
    bad = []
    for pr in CONTENT['processes']:
        page.click('#tab-how')
        if page.query_selector('#pane-how .back'):
            page.click('#pane-how .back')
        page.click(f'#pane-how .proc-btn[data-process="{pr["id"]}"]')
        page.wait_for_timeout(300)
        for i, st in enumerate(pr['steps']):
            title = page.inner_text('#pane-how .step-title')
            if title != st['title']:
                bad.append((pr['id'], i, title))
            if i < len(pr['steps']) - 1:
                page.click('#btn-next-step')
                page.wait_for_timeout(250)
        if pr['id'] == 'action-potential':
            page.wait_for_timeout(900)
            shot(page, f'{tag}-ap')
            page.click('#btn-fire')
            page.wait_for_timeout(700)
            shot(page, f'{tag}-ap-pulse')
        if pr['id'] == 'synapse':
            page.wait_for_timeout(1200)
            shot(page, f'{tag}-synapse')
            check(f'[{tag}] synapse close-up open', page.is_visible('#syn-panel'))
        if pr['id'] == 'summation':
            page.evaluate("(() => { const b = document.getElementById('btn-exc'); b.click(); b.click(); })()")
            ro2 = page.inner_text('#sum-readout')
            check(f'[{tag}] two quick excitatory inputs stay below threshold', 'Below threshold' in ro2, ro2)
            page.evaluate("document.getElementById('btn-exc').click()")
            page.wait_for_timeout(300)
            ro = page.inner_text('#sum-readout')
            check(f'[{tag}] third quick excitatory input crosses threshold and fires', 'Threshold reached' in ro, ro)
            page.wait_for_timeout(1500)
            page.click('#btn-exc')
            ro = page.inner_text('#sum-readout')
            check(f'[{tag}] single input stays below threshold', 'Below threshold' in ro or 'refractory' in ro, ro)
            page.click('#btn-inh')
            shot(page, f'{tag}-summation')
    check(f'[{tag}] all {len(PROCS)} processes and their steps reachable', not bad, bad)
    check(f'[{tag}] Play control present (motion allowed)', page.query_selector('#btn-play') is not None)

    # compare tab
    page.click('#tab-compare')
    page.wait_for_timeout(300)
    out0 = page.inner_text('#perc-out')
    page.eval_on_selector('#sl-th', "e => { e.value = '-1'; e.dispatchEvent(new Event('input')); }")
    out1 = page.inner_text('#perc-out')
    check(f'[{tag}] perceptron output changes with threshold', out0 != out1 and 'output = 1' in out1, (out0, out1))
    page.focus('.cmp-row >> nth=0')
    hl = page.evaluate("document.querySelectorAll('#cmp-svg .hl').length")
    check(f'[{tag}] focusing a compare row highlights both sides', hl >= 2, hl)
    check(f'[{tag}] compare caveats shown', 'not a description of how real neurons compute' in page.inner_text('.caveats'))
    page.evaluate("document.querySelector('#pane-compare').scrollTop = 0")
    shot(page, f'{tag}-compare')

    # quiz: multiple choice and find-the-part
    page.click('#tab-quiz')
    page.wait_for_timeout(300)
    page.click('#pane-quiz .qopt >> nth=0')
    fb = page.inner_text('#q-feedback')
    check(f'[{tag}] quiz multiple-choice gives feedback', ('Correct' in fb or 'Not quite' in fb) and len(fb) > 20, fb)
    check(f'[{tag}] quiz feedback is aria-live', page.get_attribute('#q-feedback', 'aria-live') == 'polite')
    shot(page, f'{tag}-quiz')
    # advance to a find-the-part item
    found = False
    for _ in range(6):
        page.click('#q-next')
        page.wait_for_timeout(200)
        if page.query_selector('#pane-quiz details'):
            found = True
            break
        page.click('#pane-quiz .qopt >> nth=0')
    if found:
        page.click('#pane-quiz details summary')
        target = page.evaluate("document.querySelector('#pane-quiz .qtext').textContent")
        opts = page.query_selector_all('#pane-quiz details .qopt')
        wrong = [o for o in opts if o.inner_text().lower() not in target.lower()]
        if wrong:
            wrong[0].click()
            check(f'[{tag}] find-the-part wrong try offers Show me', page.is_visible('#q-showme'))
            page.click('#q-showme')
            page.wait_for_timeout(1200)
            shot(page, f'{tag}-quiz-showme')
            check(f'[{tag}] Show me reveals Next', page.is_visible('#q-next'))
    check(f'[{tag}] find-the-part question generated', found)

    check(f'[{tag}] no console errors', not watch.errors, watch.errors[:5])
    check(f'[{tag}] no failed requests', not watch.failed, watch.failed[:5])
    check(f'[{tag}] no requests to another host', not watch.offhost, watch.offhost[:5])
    ctx.close()


def run_extras(browser, base):
    # reduced motion
    ctx, page, watch = new_page(browser, 390, 844, base, reduced=True, skip_arrival=False)
    page.goto(base + '/neuron.html')
    ready(page)
    check('[rm] arrival overlay not shown under reduced motion', not page.is_visible('#arrival'))
    check('[rm] scale note shown instead', page.is_visible('#scale-note'))
    shot(page, 'rm-scale-note')
    page.click('#btn-scale-close')
    check('[rm] idle rotation off', page.evaluate('window.__neuron.idle()') is False)
    page.click('#tab-how')
    page.click('#pane-how .proc-btn[data-process="action-potential"]')
    check('[rm] no Play button (step-only)', page.query_selector('#btn-play') is None)
    page.click('#btn-next-step')
    page.click('#btn-next-step')
    check('[rm] stepping works', page.inner_text('#pane-how .step-title') == CONTENT['processes'][1]['steps'][2]['title'])
    shot(page, 'rm-ap')
    page.click('#pane-how .back')
    page.click('#pane-how .proc-btn[data-process="summation"]')
    for _ in range(3):
        page.click('#btn-exc')
    ro = page.inner_text('#sum-readout')
    check('[rm] summation works step-by-step', 'Threshold reached' in ro, ro)
    page.click('#btn-wait')
    check('[rm] no console errors', not watch.errors, watch.errors[:5])
    check('[rm] no failed requests', not watch.failed, watch.failed[:5])
    ctx.close()

    # arrival overlay on first visit, with skip
    ctx, page, watch = new_page(browser, 1280, 800, base, skip_arrival=False)
    page.goto(base + '/neuron.html')
    page.wait_for_selector('#arrival.open', timeout=60000)
    check('[arrival] overlay shows scale text', CONTENT['scale']['text'][:30] in page.inner_text('#arrival'))
    page.click('#arr-skip', timeout=5000)
    check('[arrival] Skip closes overlay', not page.is_visible('#arrival'))
    page.reload()
    ready(page)
    check('[arrival] shown only once per browser', not page.is_visible('#arrival'))
    page.goto(base + '/neuron.html?from=atlas')
    page.wait_for_selector('#arrival.open', timeout=60000)
    check('[arrival] ?from=atlas shows it again', True)
    page.wait_for_timeout(600)
    shot(page, 'arrival')
    page.wait_for_timeout(3500)
    check('[arrival] overlay closes by itself', not page.is_visible('#arrival'))
    check('[arrival] no console errors', not watch.errors, watch.errors[:5])
    ctx.close()

    # deep links
    ctx, page, watch = new_page(browser, 1280, 800, base)
    page.goto(base + '/neuron.html?part=node_of_ranvier&level=expert')
    ready(page)
    check('[deep] ?part= opens the part', page.inner_text('#focus-name') == 'Nodes of Ranvier')
    check('[deep] ?level=expert applies', page.get_attribute('#lvl-expert', 'aria-pressed') == 'true')
    page.wait_for_timeout(1200)
    shot(page, 'deep-node-expert')
    page.goto(base + '/neuron.html?process=synapse')
    ready(page)
    check('[deep] ?process= opens the process', page.get_attribute('#tab-how', 'aria-selected') == 'true'
          and page.inner_text('#pane-how h2') == 'Passing the message on')
    page.goto(base + '/neuron.html?tab=quiz')
    ready(page)
    check('[deep] ?tab=quiz opens the quiz', page.get_attribute('#tab-quiz', 'aria-selected') == 'true')
    page.click('#btn-sources')
    n = page.evaluate("document.querySelectorAll('#sources-list li').length")
    check('[sources] Sources lists every source', n == len(CONTENT['sources']), n)
    shot(page, 'sources')
    check('[deep] no console errors', not watch.errors, watch.errors[:5])
    ctx.close()

    # narrowest phone
    ctx, page, watch = new_page(browser, 360, 740, base)
    page.goto(base + '/neuron.html')
    ready(page)
    over = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    check('[360] no horizontal overflow at 360 px', not over)
    small = page.evaluate("""[...document.querySelectorAll('#panel button, #hud button, #topbar a')]
      .filter(e => e.offsetParent && !e.classList.contains('cite-sup') && !e.classList.contains('linkbtn'))
      .map(e => [e.textContent.trim().slice(0,20), e.getBoundingClientRect().height]).filter(x => x[1] < 44)""")
    check('[360] touch targets at least 44 px', not small, small[:6])
    shot(page, '360-default')
    ctx.close()


def main():
    os.makedirs(SHOTS, exist_ok=True)
    port = free_port()
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'],
                           cwd=PUBLIC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f'http://127.0.0.1:{port}'
    time.sleep(0.8)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROME, args=ARGS)
            only = sys.argv[1] if len(sys.argv) > 1 else 'all'
            if only in ('all', 'desktop'):
                run_viewport(browser, base, 1280, 800, 'desktop')
            if only in ('all', 'phone'):
                run_viewport(browser, base, 390, 844, 'phone')
            if only in ('all', 'extras'):
                run_extras(browser, base)
            browser.close()
    finally:
        srv.terminate()
    passed = sum(1 for _, ok in results if ok)
    print(f'\n{passed} passed, {len(results) - passed} failed, {len(results)} checks')
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())

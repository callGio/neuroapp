"""Tier 7 checks: installable web app (manifest, icons), CSP, service worker,
offline pages, offline atlas, and the models cache surviving a version bump.

Run:  python3 scripts/tests/test_pwa.py
Slow: the atlas loads twice under swiftshader (1 to 2 minutes each).
"""
import io, json, os, re, shutil, socket, subprocess, tempfile, time, urllib.request
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

PUB = Path(__file__).resolve().parents[2] / 'viewer' / 'public'
ARGS = ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
PAGES = ['index.html', 'atlas-viewer.html', 'neuron.html', 'imaging.html', 'privacy.html']
OFFLINE_MSG = "You're offline. Open the atlas once while online and it will work offline after that."
PROFILE = ("try{localStorage.setItem('neuroapp.profile.v1',JSON.stringify({level:'beginner',onboarded:true,seen:{}}));"
           "sessionStorage.setItem('gyrafold.guide.hello','1')}catch(e){}")

ok, bad = [], []
def chk(name, cond, info=''):
    (ok if cond else bad).append(name)
    print(('PASS ' if cond else 'FAIL ') + name + (('  ' + str(info)) if (info and not cond) else ''), flush=True)

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def serve(root, port):
    srv = subprocess.Popen(['python3', '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=str(root),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try: urllib.request.urlopen(f'http://127.0.0.1:{port}/sw.js', timeout=1); break
        except Exception: time.sleep(0.1)
    return srv

PORT = free_port()
B = f'http://127.0.0.1:{PORT}/'
srv = serve(PUB, PORT)

def get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r: return r.status, r.read()
    except Exception as e: return getattr(e, 'code', 0), b''

def sw_shell_list():
    src = (PUB / 'sw.js').read_text()
    block = re.search(r'const SHELL = \[(.*?)\];', src, re.S).group(1)
    return re.findall(r'"([^"]+)"', block)

def wait_controlled(pg, secs=30):
    for _ in range(secs * 4):
        if pg.evaluate("!!navigator.serviceWorker.controller"): return True
        pg.wait_for_timeout(250)
    return False

def atlas_done(pg, secs=240):
    """Wait until every model has loaded or failed (status line), and the loader is gone."""
    for _ in range(secs):
        st = pg.evaluate("(()=>{const s=document.getElementById('status');return s?s.textContent:''})()")
        if not pg.evaluate("!!document.getElementById('loader')") and re.search(r'All \d+ meshes|Saved for offline|Done:', st):
            return st
        pg.wait_for_timeout(1000)
    return None

def models_cached(pg):
    return pg.evaluate("""(async()=>{ if(!(await caches.has('gyrafold-models-v1'))) return 0;
        const c=await caches.open('gyrafold-models-v1'); return (await c.keys()).length; })()""")

try:
    # ── 1. Manifest and files ──────────────────────────────────────────────
    st, body = get(B + 'manifest.webmanifest')
    try: man = json.loads(body); parsed = True
    except Exception: man = {}; parsed = False
    chk('manifest served and parses', st == 200 and parsed)
    req = {'name': 'Gyrafold', 'short_name': 'Gyrafold', 'id': '/', 'start_url': './index.html', 'scope': './',
           'display': 'standalone', 'background_color': '#060912', 'theme_color': '#0b1120', 'orientation': 'any',
           'lang': 'en', 'dir': 'ltr'}
    chk('manifest required fields', all(man.get(k) == v for k, v in req.items()) and man.get('description')
        and man.get('categories') == ['education', 'science'], {k: man.get(k) for k in req})
    icons = man.get('icons', [])
    need = {('192x192', 'any'), ('512x512', 'any'), ('192x192', 'maskable'), ('512x512', 'maskable')}
    chk('manifest has 192/512 any + maskable icons', need <= {(i['sizes'], i.get('purpose', 'any')) for i in icons})
    for i in icons + [{'src': './assets/icons/apple-touch-icon-180.png', 'sizes': '180x180'}]:
        st, data = get(B + i['src'].lstrip('./'))
        size = Image.open(io.BytesIO(data)).size if st == 200 else None
        w, h = map(int, i['sizes'].split('x'))
        chk(f"icon {i['src']} 200 and {i['sizes']}", st == 200 and size == (w, h), (st, size))
    shots = man.get('screenshots', [])
    chk('screenshots: >=1 wide and >=1 narrow', {'wide', 'narrow'} <= {s.get('form_factor') for s in shots})
    for s in shots:
        st, data = get(B + s['src'].lstrip('./'))
        size = Image.open(io.BytesIO(data)).size if st == 200 else None
        w, h = map(int, s['sizes'].split('x'))
        chk(f"screenshot {s['src']} 200, {s['sizes']}, <400KB", st == 200 and size == (w, h) and len(data) < 400_000, (st, size, len(data)))
    sc = man.get('shortcuts', [])
    chk('3 shortcuts', [x['url'] for x in sc] == ['./atlas-viewer.html', './neuron.html', './imaging.html'])
    for x in sc:
        chk(f"shortcut {x['url']} 200", get(B + x['url'].lstrip('./'))[0] == 200)

    for p in PAGES:
        html = (PUB / p).read_text()
        csp = re.search(r'Content-Security-Policy"\s*content="([^"]*)"', html)
        chk(f'{p}: links manifest, theme-color, apple-touch-icon',
            'rel="manifest" href="./manifest.webmanifest"' in html and 'name="theme-color"' in html and 'rel="apple-touch-icon"' in html)
        chk(f'{p}: CSP has manifest-src', bool(csp) and "manifest-src 'self'" in csp.group(1))
        chk(f'{p}: registers ./sw.js', 'serviceWorker.register("./sw.js")' in html)
    chk('atlas favicon is real', 'href="data:,"' not in (PUB / 'atlas-viewer.html').read_text())

    shell = sw_shell_list()
    missing = [u for u in shell if not (PUB / u.lstrip('./')).is_file()]
    chk('every precache URL exists on disk', not missing, missing)
    size_mb = sum((PUB / u.lstrip('./')).stat().st_size for u in shell) / 1e6
    print(f'  precache: {len(shell)} files, {size_mb:.2f} MB')
    chk('precache is small (<5 MB) and has no models', size_mb < 5 and not any(u.endswith('.glb') for u in shell))
    chk('privacy.html precached', './privacy.html' in shell)

    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=ARGS)

        # ── 2. Online pages: SW, console, CSP, other origins ───────────────
        ctx = br.new_context(viewport={'width': 1024, 'height': 700})
        ctx.add_init_script(PROFILE)
        ctx.add_init_script("window.__csp=[];document.addEventListener('securitypolicyviolation',e=>window.__csp.push(e.violatedDirective+' '+e.blockedURI))")
        ext, errs, perrs = [], [], []
        ctx.on('request', lambda r: ext.append(r.url) if not r.url.startswith(B) and not r.url.startswith(('data:', 'blob:')) else None)
        pg = ctx.new_page(); pg.set_default_timeout(240000)
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: perrs.append(str(e)))

        pg.goto(B + 'index.html')
        chk('service worker controls the page', wait_controlled(pg))
        state = pg.evaluate("navigator.serviceWorker.getRegistration().then(r=>r&&r.active&&r.active.state)")
        chk('service worker activated', state == 'activated', state)
        keys = pg.evaluate("caches.keys()")
        chk('shell cache created', any(k.startswith('gyrafold-shell-') for k in keys), keys)
        n_shell = pg.evaluate("""(async()=>{const k=(await caches.keys()).find(n=>n.startsWith('gyrafold-shell-'));
            return (await (await caches.open(k)).keys()).length})()""")
        chk('every shell file precached', n_shell >= len(shell), (n_shell, len(shell)))

        # install button: hidden by default; appears on beforeinstallprompt
        chk('install button hidden without prompt event', pg.locator('#cta-install').is_hidden())
        chk('iOS tip hidden on non-iOS', pg.locator('#ios-install-tip').is_hidden())
        pg.evaluate("""(()=>{const e=new Event('beforeinstallprompt',{cancelable:true});
            e.prompt=()=>{window.__prompted=true;return Promise.resolve()};e.userChoice=Promise.resolve({outcome:'dismissed'});
            window.dispatchEvent(e)})()""")
        bb = pg.locator('#cta-install').bounding_box()
        chk('install button shows on beforeinstallprompt, >=44px', pg.locator('#cta-install').is_visible() and bb and bb['height'] >= 44, bb)
        pg.wait_for_timeout(4500)
        pg.screenshot(path='/tmp/pwa_install_button.png')
        pg.click('#cta-install'); pg.wait_for_timeout(200)
        chk('install button prompts then hides', pg.evaluate('window.__prompted===true') and pg.locator('#cta-install').is_hidden())

        content_checks = {
            # the stats strip counts up from the lesson JSON once scrolled into view
            'index.html': "document.body.innerText.includes('Explore the human brain') && !document.getElementById('stats-strip').classList.contains('hidden') && /\\d/.test(document.getElementById('stat-lessons').textContent)",
            'neuron.html': "document.body.innerText.includes('Cell body (soma)')",
            'imaging.html': "document.getElementById('intro').textContent.trim().length>20",
            'privacy.html': "document.querySelector('h1').textContent==='Privacy' && document.body.innerText.includes('neuroapp.')",
        }
        for p, js in content_checks.items():
            pg.goto(B + p); pg.wait_for_timeout(1500)
            pg.evaluate("document.getElementById('stats-strip')&&document.getElementById('stats-strip').scrollIntoView()"); pg.wait_for_timeout(2500)
            chk(f'online {p}: content renders', pg.evaluate(js))
            csp = pg.evaluate('window.__csp')
            chk(f'online {p}: no CSP violations', not csp, csp)
        chk('online pages: no console errors', not errs, errs[:5])
        chk('online pages: no page errors', not perrs, perrs[:5])

        # ── 3. Offline pages ───────────────────────────────────────────────
        ctx.set_offline(True)
        for p, js in content_checks.items():
            q = '?part=soma' if p == 'neuron.html' else ''
            try:
                pg.goto(B + p + q); pg.wait_for_timeout(1500)
                pg.evaluate("document.getElementById('stats-strip')&&document.getElementById('stats-strip').scrollIntoView()"); pg.wait_for_timeout(2500)
                good = pg.evaluate(js)
            except Exception as e:
                good = False; print('   ', e)
            chk(f'offline {p}{q}: content renders', good)
            chk(f'offline {p}: lesson JSON loads', pg.evaluate("""fetch('./content/learning.json').then(r=>r.json()).then(d=>Array.isArray(d.topics)&&d.topics.length>0).catch(()=>false)"""))
        pg.goto(B + 'not-a-page.html'); pg.wait_for_timeout(1500)
        chk('offline unknown URL falls back to index', 'Explore the human brain' in pg.evaluate('document.body.innerText'))
        ctx.set_offline(False)

        # ── 4. Atlas: full online load, then offline ───────────────────────
        errs.clear(); perrs.clear()
        pg.goto(B + 'atlas-viewer.html'); t0 = time.time()
        st = atlas_done(pg)
        print(f'  atlas online load: {time.time()-t0:.0f}s, status: {st!r}')
        chk('atlas loads online', bool(st) and 'failed' not in st, st)
        n = 0
        for _ in range(90):
            n = models_cached(pg)
            if n >= 328: break
            pg.wait_for_timeout(1000)
        chk('all 328 models in gyrafold-models-v1 after one online load', n >= 328, n)
        chk('atlas online: no CSP violations', not pg.evaluate('window.__csp'), pg.evaluate('window.__csp'))
        chk('atlas online: no console errors / page errors', not errs and not perrs, (errs[:3], perrs[:3]))
        chk('storage.persist available (called after load)', pg.evaluate("!!(navigator.storage&&navigator.storage.persist)"))

        ctx.set_offline(True)
        pg.reload(); t0 = time.time()
        st = atlas_done(pg)
        print(f'  atlas offline load: {time.time()-t0:.0f}s, status: {st!r}')
        chk('atlas loads fully offline', bool(st) and 'failed' not in st and 'offline.' not in st, st)
        pg.fill('#search', 'hippocampus'); pg.wait_for_timeout(400)
        pg.locator('#search-results .sr-item').first.dispatch_event('mousedown'); pg.wait_for_timeout(1200)
        name = pg.evaluate("document.getElementById('focus-header-name').textContent")
        chk('offline atlas: a structure can be selected', 'hippocampus' in name.lower(), name)
        pg.screenshot(path='/tmp/pwa_offline_atlas.png')
        ctx.set_offline(False)

        # ── 5. Version bump: shell caches replaced, models cache kept ──────
        tmp = Path(tempfile.mkdtemp(prefix='gyrafold-bump-'))
        for e in PUB.iterdir():
            if e.name != 'sw.js': os.symlink(e, tmp / e.name)
        src = (PUB / 'sw.js').read_text()
        old_v = re.search(r'const VERSION = "([^"]+)"', src).group(1)
        (tmp / 'sw.js').write_text(src.replace(f'const VERSION = "{old_v}"', 'const VERSION = "test-bump"'))
        srv.kill(); srv.wait(); srv = serve(tmp, PORT)
        pg.goto(B + 'index.html'); wait_controlled(pg)
        pg.evaluate("navigator.serviceWorker.getRegistration().then(r=>r.update())")
        # the new worker takes over on its own once its shell is fully cached
        keys = []
        for _ in range(80):
            keys = pg.evaluate("caches.keys()")
            if 'gyrafold-shell-test-bump' in keys and f'gyrafold-shell-{old_v}' not in keys: break
            pg.wait_for_timeout(250)
        print('  caches after bump:', keys)
        chk('old shell cache deleted, new one created', 'gyrafold-shell-test-bump' in keys and f'gyrafold-shell-{old_v}' not in keys)
        chk('models cache survives the version bump', 'gyrafold-models-v1' in keys and models_cached(pg) >= 328)
        srv.kill(); srv.wait(); shutil.rmtree(tmp); srv = serve(PUB, PORT)
        ctx.close()

        # ── 6. Offline atlas with an empty models cache ────────────────────
        ctx = br.new_context(viewport={'width': 1024, 'height': 700}); ctx.add_init_script(PROFILE)
        ctx.on('request', lambda r: ext.append(r.url) if not r.url.startswith(B) and not r.url.startswith(('data:', 'blob:')) else None)
        pg = ctx.new_page(); pg.set_default_timeout(120000)
        pg.goto(B + 'index.html'); wait_controlled(pg)
        ctx.set_offline(True)
        pg.goto(B + 'atlas-viewer.html')
        txt = ''
        for _ in range(60):
            txt = pg.evaluate("(()=>{const s=document.getElementById('loader-status');return s?s.textContent:''})()")
            if txt == OFFLINE_MSG: break
            pg.wait_for_timeout(500)
        chk('offline + empty models cache: plain offline message', txt == OFFLINE_MSG, txt)
        chk('offline message: progress bar hidden, loader stays', pg.evaluate(
            "getComputedStyle(document.getElementById('loader-bar-wrap')).display==='none' && !!document.getElementById('loader')"))
        chk('empty-cache run fetched no models', models_cached(pg) == 0)
        pg.screenshot(path='/tmp/pwa_offline_message.png')
        ctx.close()
        br.close()

    chk('zero requests to other origins', not ext, sorted(set(ext))[:5])
finally:
    srv.kill()

print(f'\n{len(ok)} passed, {len(bad)} failed')
if bad: print('FAILED:', bad)
raise SystemExit(1 if bad else 0)

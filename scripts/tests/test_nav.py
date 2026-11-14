import subprocess,time,math
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8942'],cwd='/home/claude/neuroapp/viewer/public',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
ARGS=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']
ok=[];bad=[]
def chk(n,c):
    (ok if c else bad).append(n); print(('PASS ' if c else 'FAIL ')+n)
def clk(sel):
    r=pg.evaluate('''s=>{const e=document.querySelector(s);const b=e.getBoundingClientRect();const t=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);return t&&(t===e||e.contains(t))}''',sel)
    if not r: print('  covered:',sel)
    pg.evaluate('s=>document.querySelector(s).click()',sel)
def ready(pg):
    for _ in range(120):
        if pg.evaluate("(()=>{const l=document.getElementById('loader');return !l||getComputedStyle(l).display=='none'||getComputedStyle(l).opacity=='0'})()"): break
        pg.wait_for_timeout(1000)
    pg.wait_for_timeout(1500)
    for sel in ['#onboard-close','.onboard-skip']:
        try:
            if pg.locator(sel).first.is_visible(): pg.locator(sel).first.click()
        except Exception: pass
S="window.__s=()=>({sel:document.getElementById('focus-header-name').textContent, page:getComputedStyle(document.getElementById('focus-page')).display, back:!document.getElementById('nav-back').hidden, hash:location.hash})"
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=ARGS)
    c=b.new_context(viewport={'width':1366,'height':800}); pg=c.new_page(); errs=[]
    pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.add_init_script("try{localStorage.setItem('neuroapp.level','new');localStorage.setItem('neuroapp.onboarded','1')}catch(e){}")
    pg.goto('http://127.0.0.1:8942/index.html'); pg.goto('http://127.0.0.1:8942/atlas-viewer.html'); ready(pg)
    pg.evaluate(S)
    chk('main menu visible', pg.locator('#nav-home').is_visible())
    chk('back hidden at start', pg.locator('#nav-back').is_hidden())
    cam0=pg.evaluate("1")
    cv=pg.locator('#c').bounding_box()
    pg.mouse.click(cv['x']+cv['width']*.5, cv['y']+cv['height']*.45); pg.wait_for_timeout(1200)
    s1=pg.evaluate('__s()'); print(s1)
    chk('click selects + back appears', s1['page']=='flex' and s1['back'])
    def search(term):
        pg.fill('#search',term); pg.wait_for_timeout(300)
        pg.locator('#search-results .sr-item').first.dispatch_event('mousedown'); pg.wait_for_timeout(900)
    search('hippocampus'); sA=pg.evaluate('__s()')
    search('cerebellum'); sB=pg.evaluate('__s()'); print(sA['sel'],'->',sB['sel'])
    clk('#nav-back'); pg.wait_for_timeout(900)
    chk('back returns to previous structure', pg.evaluate('__s()')['sel']==sA['sel'])
    clk('#foc-isolate')
    pg.wait_for_timeout(400)
    vis=lambda: pg.evaluate("(()=>{let n=0;document.querySelectorAll('x');return 0})()")
    clk('#nav-back'); pg.wait_for_timeout(900)
    chk('back after isolate keeps structure', pg.evaluate('__s()')['sel']==sA['sel'])
    chk('reset visible when selected', pg.locator('#nav-reset').is_visible())
    clk('#nav-reset'); pg.wait_for_timeout(900)
    r=pg.evaluate('__s()'); chk('reset clears to whole brain + hides itself', r['page']=='none' and pg.locator('#nav-reset').is_hidden() and r['back'])
    clk('#nav-back'); pg.wait_for_timeout(900)
    chk('back undoes reset', pg.evaluate('__s()')['sel']==sA['sel'])
    # browser back
    pg.go_back(); pg.wait_for_timeout(900)
    chk('browser back steps view, stays in atlas', 'atlas-viewer' in pg.url and pg.evaluate('__s()')['sel']==s1['sel'])
    clk('#nav-back'); pg.wait_for_timeout(900)
    s0=pg.evaluate('__s()'); print(s0)
    chk('back to whole brain', s0['page']=='none' and not s0['back'])
    pg.mouse.click(cv['x']+cv['width']*.5, cv['y']+cv['height']*.45); pg.wait_for_timeout(1000)
    pg.screenshot(path='/home/claude/stage/nav/after_d.png')
    clk('#focus-back-btn'); pg.wait_for_timeout(800)
    chk('panel back works', pg.evaluate('__s()')['page']=='none')
    # quiz hides nav
    clk('.ptab[data-pane="pane-quiz"]'); pg.wait_for_timeout(300)
    clk('#btn-start-quiz'); pg.wait_for_timeout(1500)
    chk('quiz: home stays, back/reset hidden', pg.locator('#nav-home').is_visible() and not pg.locator('#nav-back').is_visible() and not pg.locator('#nav-reset').is_visible()); pg.screenshot(path='/home/claude/stage/nav/after_quiz.png')
    clk('#btn-quit-quiz'); pg.wait_for_timeout(800)
    chk('nav back after quiz', pg.locator('#nav-home').is_visible())
    clk('#nav-home'); pg.wait_for_timeout(4000); print('URL',pg.url)
    chk('home goes to welcome', pg.url.endswith('/index.html'))
    chk('no page errors', not errs); print(errs[:3])
    c.close()
    c=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True); pg=c.new_page()
    pg.add_init_script("try{localStorage.setItem('neuroapp.level','new');localStorage.setItem('neuroapp.onboarded','1')}catch(e){}")
    pg.goto('http://127.0.0.1:8942/atlas-viewer.html'); ready(pg)
    cv=pg.locator('#c').bounding_box(); pg.touchscreen.tap(cv['x']+cv['width']*.5, cv['y']+cv['height']*.35); pg.wait_for_timeout(1200)
    bb=pg.locator('#nav-back').bounding_box(); hb=pg.locator('#nav-home').bounding_box(); rb=pg.locator('#nav-reset').bounding_box(); chk('phone nav fits', rb and rb['x']+rb['width']<=390)
    chk('phone buttons visible >=44px', bb and hb and bb['height']>=44 and hb['height']>=44)
    pg.screenshot(path='/home/claude/stage/nav/after_m.png')
    clk('#nav-back'); pg.wait_for_timeout(900)
    chk('phone back clears', pg.locator('#nav-back').is_hidden())
    for f in ['neuron.html','imaging.html']:
        pg.goto('http://127.0.0.1:8942/'+f); pg.wait_for_timeout(2500)
        h=pg.locator('nav.modes a[href="./index.html"]'); bx=h.bounding_box()
        chk(f+' home link visible on phone', h.is_visible() and bx['x']>=0 and bx['x']+bx['width']<=390 and pg.evaluate('document.documentElement.scrollWidth')<=390)
        pg.screenshot(path='/home/claude/stage/nav/'+f+'_m.png')
    b.close()
srv.kill(); print(len(ok),'pass',len(bad),'fail')

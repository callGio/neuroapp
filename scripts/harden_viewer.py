#!/usr/bin/env python3
"""Security hardening for viewer/public/atlas-viewer.html (idempotent).

1. Load three.js from the vendored, checksum-verified copy instead of a CDN.
2. Add a Content Security Policy that only allows the page's own files.
3. Allow only http(s) URLs in links built from data files (safeUrl).
4. Build the footer with DOM APIs instead of an HTML string.
5. Reject saved progress/profile data that is not a plain object.
"""
import re
import sys

path = sys.argv[1]
s = open(path, encoding="utf-8").read()
orig = s
log = []

# 1. vendored three.js
cdn = re.compile(r'"three":\s*"https://cdn\.jsdelivr\.net/npm/three@0\.160\.1/build/three\.module\.js"')
if cdn.search(s):
    s = cdn.sub('"three": "./vendor/three/build/three.module.js"', s)
    s = re.sub(r'"three/addons/":\s*"https://cdn\.jsdelivr\.net/npm/three@0\.160\.1/examples/jsm/"',
               '"three/addons/": "./vendor/three/examples/jsm/"', s)
    log.append("import map -> vendored three.js")
if "cdn.jsdelivr" in s:
    sys.exit("ERROR: CDN reference still present after rewrite")

# 2. CSP
CSP = ('<meta http-equiv="Content-Security-Policy" content="'
       "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: blob:; connect-src 'self' blob: data:; worker-src 'self' blob:; "
       "object-src 'none'; base-uri 'none'; form-action 'none'\">")
if "Content-Security-Policy" not in s:
    s = s.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">\n' + CSP, 1)
    if "Content-Security-Policy" not in s:
        sys.exit("ERROR: could not insert CSP (no <meta charset=\"UTF-8\">)")
    log.append("CSP meta added")
if '<meta name="referrer"' not in s:
    s = s.replace(CSP, CSP + '\n<meta name="referrer" content="no-referrer">', 1)
    log.append("referrer policy added")

# 3. safeUrl helper, placed right after escHtml
SAFE = '''
// Only http(s) links may be built from data files (blocks javascript:, data:, etc.)
function safeUrl(u) {
  try {
    const url = new URL(String(u), window.location.href);
    return (url.protocol === 'https:' || url.protocol === 'http:') ? url.href : null;
  } catch (e) { return null; }
}
'''
if "function safeUrl(" not in s:
    m = re.search(r"function escHtml\(s\) \{.*?\n\}\n", s, re.S)
    if not m:
        sys.exit("ERROR: escHtml not found")
    s = s[:m.end()] + SAFE + s[m.end():]
    log.append("safeUrl() added")

# wrap .href assignments from data
n_before = s.count("safeUrl(")
s = re.sub(r"(\b\w+)\.href(\s*)=(\s*)(src\.url|a\.license_url|a\.citation_url|atlas\.license_url|atlas\.citation_url)\s*;",
           r"\1.href\2=\3safeUrl(\4) || '#';", s)
if s.count("safeUrl(") > n_before:
    log.append(f"wrapped {s.count('safeUrl(') - n_before} data-derived hrefs")

# 4. footer via DOM
old_footer = re.search(r"function setupFooter\(atlas\) \{.*?\n\}\n", s, re.S)
if old_footer and "innerHTML" in old_footer.group(0):
    new_footer = '''function setupFooter(atlas) {
  const f = document.getElementById('footer');
  f.textContent = '';
  const strong = document.createElement('strong');
  strong.textContent = atlas.name || 'Atlas';
  f.appendChild(strong);
  [['License', atlas.license_url], ['Citation', atlas.citation_url]].forEach(([label, url]) => {
    const href = safeUrl(url);
    if (!href) return;
    f.appendChild(document.createTextNode(' · '));
    const a = document.createElement('a');
    a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer';
    a.textContent = label;
    f.appendChild(a);
  });
}
'''
    s = s[:old_footer.start()] + new_footer + s[old_footer.end():]
    log.append("footer rebuilt with DOM APIs")

# 5. validate parsed storage
pairs = [("srsData = raw ? JSON.parse(raw) : {};",
          "srsData = raw ? JSON.parse(raw) : {};\n    if (!srsData || typeof srsData !== 'object' || Array.isArray(srsData)) srsData = {};"),
         ("if (raw) learnerProfile = JSON.parse(raw);",
          "if (raw) { const p = JSON.parse(raw); if (p && typeof p === 'object' && !Array.isArray(p)) learnerProfile = p; }")]
for a, b in pairs:
    if a in s and b not in s:
        s = s.replace(a, b, 1)
        log.append("storage validation: " + a.split('=')[0].strip())

if s != orig:
    open(path, "w", encoding="utf-8").write(s)
print("\n".join(log) if log else "no changes (already hardened)")

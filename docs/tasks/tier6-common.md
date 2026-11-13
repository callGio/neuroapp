# Tier 6: neuron mode, brain-imaging page, pathways (shared rules)

NeuroApp gains two new pages next to the atlas viewer:

- `viewer/public/neuron.html`  (spec: `tier6-neuron.md`)
- `viewer/public/imaging.html` (spec: `tier6-imaging.md`)

Each page is one self-contained HTML file (inline `<style>` and one inline
`<script type="module">`), reading its text from a JSON file in `viewer/public/content/`.
Do not edit `atlas-viewer.html`, `index.html` or `content/learning.json`; the lead does that.

## Audience

The owner is new to neuroscience. A first-time learner must be able to use every screen
without prior knowledge, and an expert must not be bored: every topic has a `beginner` and
an `expert` level, switched by one control, remembered in `localStorage` under the existing
key the viewer uses (grep `PROFILE_KEY` / `level` in `atlas-viewer.html` and reuse the same
key and values so the level carries across pages; wrap storage in try/catch).

## Hard rules

- No external requests: no CDNs, web fonts, analytics or remote images. Everything is served
  from `viewer/public/`. three.js is vendored at `./vendor/three/` (r160); use the same
  import map as `atlas-viewer.html`.
- CSP meta tag, copied from `atlas-viewer.html` (same policy string), plus
  `<meta name="referrer" content="no-referrer">`.
- Never put data into `innerHTML`. Build DOM with `createElement` + `textContent`. Copy
  `escHtml()` / `safeUrl()` from the viewer if you need them; links from JSON go through
  `safeUrl()` and get `rel="noopener noreferrer"`.
- No neuroscience facts in the HTML/JS. Every sentence that states a fact lives in the
  content JSON with a `cite` array pointing at `sources`. UI labels ("Next", "Show me") are
  fine in HTML. Anything illustrative must say so on screen ("Illustration, not to scale",
  "Synthetic signal").
- Sources must be openly readable and reputable: OpenStax (CC BY 4.0), NIH/NIBIB/NINDS pages
  (public domain), open textbooks, StatPearls, or peer-reviewed papers. Fetch each source and
  check every point against it before writing the point. Paraphrase; never copy sentences.
  Citations in APA 7. If a claim cannot be verified, leave it out. Record the URL you checked.
- Numbers (voltages, speeds, sizes, resolutions) only when the source gives them; give ranges
  as the source does and say "about".
- Distinguish established fact from simplification. Where the page simplifies, say so in a
  `caveat` field shown in the expert level.
- `prefers-reduced-motion: reduce`: no autoplay loops; animations become step-by-step
  (a "Next step" button) or static frames.
- Accessibility: keyboard reachable, visible focus rings, buttons are `<button>`, canvas
  content has a text equivalent (the side panel), contrast at least 4.5:1, `aria-live` for
  quiz feedback.
- Phones: must work at 360 px wide. Below 760 px use the same bottom-sheet idea as the
  viewer (3D on top, panel as a sheet); simple is fine: a panel that takes the lower ~45% of
  the screen and scrolls. Touch targets at least 44 px. No hover-only information.
- No `text-transform: uppercase`, no tracked-out eyebrow labels, no numbered section markers
  unless the content is a real sequence.
- Performance: runs on a mid-range phone. Keep triangle counts modest (under ~150k), cap
  `devicePixelRatio` at 2, pause the render loop when the tab is hidden.

## Design system (same as the viewer and welcome page)

Fonts in `./vendor/fonts/`:

```css
@font-face{font-family:"Inter";src:url("./vendor/fonts/inter-var.woff2") format("woff2");font-weight:100 900;font-display:swap}
@font-face{font-family:"Space Grotesk";src:url("./vendor/fonts/space-grotesk-var.woff2") format("woff2");font-weight:300 700;font-display:swap}
```

Tokens:

```css
--bg-0:#060912; --bg-1:#0b1120; --bg-2:#111a2e;
--surface:rgba(16,24,42,.72); --surface-solid:#121b30; --border:rgba(148,163,209,.16);
--text:#e8ecf6; --muted:#9aa5bd; --faint:#6b7590;
--violet:#8b6cff; --cyan:#22d3ee; --pink:#f472b6; --green:#34d399; --amber:#fbbf24; --red:#f87171;
--grad:linear-gradient(135deg,#8b6cff 0%,#22d3ee 100%);
--radius:14px; --radius-sm:10px; --shadow:0 10px 40px rgba(0,0,0,.45);
```

Header (both pages): the brand mark and wordmark exactly as in `atlas-viewer.html` (grep
`class="brand"`), linking to `./index.html`, then three mode links: "Whole brain"
(`./atlas-viewer.html`), "Neuron" (`./neuron.html`), "Imaging" (`./imaging.html`), with
`aria-current="page"` on the current one. `<link rel="icon" href="./assets/favicon.svg">`.
Footer line: "Educational use only; not medical advice." plus a "Sources" control that lists
every source used on the page (citation text + link).

Every fact shown has a small source marker; activating it shows the citation(s). Follow how
the viewer renders `cite` (grep `cite` in `atlas-viewer.html`) so it feels the same.

## Deliverables and checks (each page)

1. The HTML page and its content JSON.
2. A Playwright test in `scripts/tests/` (Python, system Chrome at `/usr/bin/google-chrome`,
   args `--use-gl=swiftshader --enable-unsafe-swiftshader`, `bypass_csp=True` only if you must
   evaluate strings; serve `viewer/public` with `python3 -m http.server`). Run it at 1280x800
   and 390x844. Assert: no console errors, no failed requests, no request to another host,
   every part/method reachable, level switch changes text, quiz answers give feedback, page
   works with `reduced_motion="reduce"`. Save screenshots to `/home/claude/stage/shots6/`.
3. Look at the screenshots yourself (Read tool) and fix what looks wrong: overlap, clipped
   text, unreadable contrast, a model that does not read as what it is.
4. A JSON validation script: every `cite` id exists in `sources`, every source has
   `citation`, `url`, `license`, no empty text.
5. Report back: what you built, what you verified against which URL, anything you left out
   because you could not verify it, and known weaknesses. Be candid; do not claim a check you
   did not run.

Do not commit, push or deploy. The lead reviews first.

## Team

The lead (Fable) wrote these specs and reviews. You (Opus) own the build. Use Sonnet
subagents for well-specified chunks (a test script, an SVG diagram, a JSON validation script)
and Haiku subagents for lookups and mechanical checks (does this URL say this, list the ids).
Give them exact files and acceptance criteria; check their work before using it. Facts stay
your responsibility.

# Tier 5: welcome page and visual redesign

Goal: the first thing a visitor sees is an inviting welcome page, and the viewer looks
polished and alive instead of plain. Work in two parts, in order. Part A is one file
(`viewer/public/index.html`); Part B edits `viewer/public/atlas-viewer.html`.

## Hard rules (both parts)

- No external requests of any kind: no CDNs, Google Fonts, analytics or images from other
  sites. Everything is served from `viewer/public/`.
- Keep every security measure: the CSP meta tag, the vendored three.js import map,
  `safeUrl()`, `escHtml()`, `isShown()`, textContent for data. Never use innerHTML with data.
- Do not write any neuroscience facts yourself. Use only the copy given in this file or
  text read from `content/learning.json` / `atlas-manifest.json` at runtime.
- Respect `prefers-reduced-motion: reduce`: no animation loops, show a static frame instead.
- Accessibility: visible focus rings, `alt` text, buttons are `<button>` or `<a>`, colour
  contrast at least 4.5:1 for body text.
- Must work on phones (the viewer already has a bottom-sheet layout below 760px; do not
  break it). Targeted edits only in atlas-viewer.html.

## Design system (use in both files)

Fonts (already in `viewer/public/vendor/fonts/`, OFL licensed):

```css
@font-face{font-family:"Inter";src:url("./vendor/fonts/inter-var.woff2") format("woff2");font-weight:100 900;font-display:swap}
@font-face{font-family:"Space Grotesk";src:url("./vendor/fonts/space-grotesk-var.woff2") format("woff2");font-weight:300 700;font-display:swap}
```

Body text: `"Inter", system-ui, sans-serif`. Headings, brand and numbers: `"Space Grotesk"`.

Tokens (put in `:root`):

```css
--bg-0:#060912; --bg-1:#0b1120; --bg-2:#111a2e;
--surface:rgba(16,24,42,.72); --surface-solid:#121b30; --border:rgba(148,163,209,.16);
--text:#e8ecf6; --muted:#9aa5bd; --faint:#6b7590;
--violet:#8b6cff; --cyan:#22d3ee; --pink:#f472b6; --green:#34d399; --amber:#fbbf24; --red:#f87171;
--grad:linear-gradient(135deg,#8b6cff 0%,#22d3ee 100%);
--radius:14px; --radius-sm:10px; --shadow:0 10px 40px rgba(0,0,0,.45);
```

Brand mark: an inline SVG (24–40px) of a stylised neuron: a circle (soma) with 5–6 curved
branches, stroked with a `linearGradient` from `#8b6cff` to `#22d3ee`. Wordmark "NeuroApp"
in Space Grotesk 600.

Buttons: primary = `background:var(--grad)`, dark text `#060912`, radius 999px, padding
12px 22px, weight 600, slight lift on hover (`translateY(-1px)` + glow
`0 8px 30px rgba(139,108,255,.35)`). Secondary = transparent, 1px `--border`, text
`--text`, hover background `rgba(255,255,255,.05)`.

## Part A: welcome page (`viewer/public/index.html`, full rewrite)

Remove the meta-refresh redirect. Keep a CSP meta tag:
`default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'`
plus `<meta name="referrer" content="no-referrer">`, a description meta tag, Open Graph
tags (`og:title` "NeuroApp: explore the human brain in 3D", `og:description` same as the
subtitle below, `og:image` `./assets/og-card.png`), and `<link rel="icon" href="./assets/favicon.svg">`.

Sections, top to bottom:

1. **Top bar**: brand mark + "NeuroApp" on the left; on the right links "Features",
   "How it works", and a small secondary button "Open the atlas" → `atlas-viewer.html`.
   Sticky, glass background (`--surface` + `backdrop-filter: blur(14px)`).

2. **Hero** (min-height 88vh):
   - Full-bleed `<canvas id="neural-bg">` behind everything: a "neural field" animation.
     About 70 nodes (35 on screens under 700px) drift slowly; draw a line between nodes
     closer than 140px with opacity falling off with distance; every ~400ms pick a random
     edge and send a glowing "spike" (small bright dot, cyan, with a short fading trail)
     along it over ~900ms; when it arrives, the target node flashes briefly. Colours:
     nodes `#8b6cff` at 70% opacity, lines `rgba(139,108,255,.18)`. Pause when the tab is
     hidden (`document.hidden`). Device-pixel-ratio aware, capped at 2. Reduced motion:
     draw one static frame.
   - Left column: eyebrow text "Free · No account · Works on your phone" (small caps,
     cyan); heading **"Explore the human brain in 3D"** (Space Grotesk, clamp(2.4rem, 6vw,
     4.4rem), the words "in 3D" filled with `--grad` via background-clip:text); subtitle
     **"Spin, slice and click through 300+ structures. Learn what each part does with cited
     lessons, take a guided tour, and quiz yourself with questions that adapt to you."**
   - Level picker under the subtitle: label "How familiar are you with neuroscience?" and
     three pill toggles (radio behaviour, `aria-pressed`): "New to it" (`beginner`), "Some
     background" (`some`), "Expert" (`expert`). Default none selected. The choice is added
     as `level=<value>` to the three hero buttons' URLs.
   - Three buttons: primary **"Start exploring"** → `atlas-viewer.html`; secondary
     **"Take the 5-minute tour"** → `atlas-viewer.html?start=tour`; secondary
     **"Quiz me"** → `atlas-viewer.html?start=quiz`.
   - Right column: `<img src="./assets/brain-lateral.webp">` (alt "3D model of the human
     brain seen from the left side, each region a different colour") with a soft radial glow
     behind it (`radial-gradient` violet→transparent) and a slow 6s float animation
     (translateY ±8px; none with reduced motion). On phones the image goes above the text
     and shrinks to 70% width.

3. **Stats strip**: three numbers in Space Grotesk with gradient text, labels underneath:
   "3D structures", "cited lessons", "guided tours". Fill them at runtime: fetch
   `./atlas-manifest.json` (count `models.length`) and `./content/learning.json` (count
   `topics.length` and `tours.length`). If a fetch fails, hide the strip. Count up from 0
   over 1s when the strip scrolls into view (IntersectionObserver); reduced motion shows
   the final numbers.

4. **Features** (`id="features"`): heading "Everything you need to learn neuroanatomy",
   four glass cards in a 2×2 grid (1 column on phones), each with an inline SVG icon in a
   gradient circle:
   - **Explore in 3D**: "Rotate, zoom and slice the brain. Isolate any region and see the
     smaller parts inside it."
   - **Learn at your level**: "Beginner and expert lessons for each structure, with every
     claim linked to its source."
   - **Practice that sticks**: "Find-it and name-it quizzes with spaced review, so you
     revisit what you are about to forget."
   - **Anywhere, free**: "Runs in your browser on a laptop or phone. No account, no
     download, no tracking."
   Cards rise and fade in on scroll (IntersectionObserver, 400ms; none with reduced motion).

5. **How it works** (`id="how-it-works"`): heading "Three steps", a horizontal row (vertical
   on phones) of numbered steps joined by a thin gradient line: "1 · Pick a region" — "Tap
   any part of the brain or search for it by name."; "2 · Read its story" — "See what it
   does, what it connects to and what happens when it is damaged."; "3 · Test yourself" —
   "Quick quizzes bring back what you missed until it sticks."

6. **Final call to action**: a wide glass panel with heading "Ready to look inside?" and the
   primary "Start exploring" button (same URL rule as the hero, including `level`).

7. **Footer** (small, `--muted`): "Built by Giovanni Callahan" linking to
   `https://giovannicallahan.github.io/`; "Source code" → `https://github.com/giovannicallahan/neuroapp`;
   "3D models: SPL/NAC Brain Atlas (Halle et al., 2017)" → `./NOTICE.html` if it exists,
   otherwise the GitHub NOTICE.md URL `https://github.com/giovannicallahan/neuroapp/blob/main/NOTICE.md`;
   and the line "For learning only. Not for medical use." All external links get
   `rel="noopener noreferrer"` and `target="_blank"`.

Background of the page: `--bg-0` with a very faint dot grid
(`radial-gradient(rgba(255,255,255,.035) 1px, transparent 1px)` at 24px) and two large
blurred colour blobs (violet top-left, cyan bottom-right, `filter: blur(120px)`, 25%
opacity). Smooth scrolling for the anchor links. Total page weight excluding images under
40 KB.

## Part B: viewer refresh (`viewer/public/atlas-viewer.html`)

Add a `/* ══ THEME ══ */` block **just before** the existing `/* ══ MOBILE LAYOUT` comment in
the `<style>` element so the mobile rules still win. Use the design system above.

1. **Fonts and tokens**: `@font-face` rules, `:root` tokens, body font Inter.

2. **Background behind the brain**: create the `WebGLRenderer` with `alpha: true` and
   `renderer.setClearColor(0x000000, 0)`; give `#canvas-wrap` the background
   `radial-gradient(ellipse at 50% 42%, #18234a 0%, #0b1120 48%, #060912 100%)` plus the same
   faint dot grid as the welcome page. Check that clipping planes, the mastery map, the
   gizmo and screenshots still work.

3. **Panel styling**: `#panel` uses `--surface` with `backdrop-filter: blur(16px)` and a
   1px `--border` right edge. Tabs: active tab gets a 2px `--grad` underline and `--text`
   colour; inactive `--muted`. All the small buttons (`.tog-btn`, `.preset-btn`, `.foc-btn`,
   `.iso-btn`, `.stab`, `.summ-btn`, `.tour-nav-btn`, `.conf-btn`, `.qopt-btn`) share one
   rounded style: `--surface-solid` fill, `--border`, radius `--radius-sm`, hover border
   `rgba(139,108,255,.55)`. Inputs and selects: same fill, focus ring `0 0 0 3px
   rgba(139,108,255,.35)`. Quiz cards (`.quiz-card`): glass with a gradient border on hover.
   Quiz HUD, tour HUD and modal boxes: glass (`--surface` + blur), radius `--radius`,
   `--shadow`. Correct answer green `--green`, wrong `--red`.

4. **Brand header**: replace the text of the `#panel-top` h1 ("Brain Atlas") with the brand
   mark SVG + "NeuroApp" wordmark, and add a small "Home" link (house icon + text) on the
   right of the header pointing to `./index.html`. On phones (`#panel-top` is hidden), add
   a "Home" link as the last item of the Tools pane instead.

5. **Loading screen**: a full-screen overlay `#loader` shown until all meshes have loaded
   (hook into the existing load-progress code that updates `#status`):
   brand mark (pulsing gently) + "NeuroApp"; a thin progress bar with `--grad` fill showing
   loaded / total models and the text "Loading 3D brain… 140 / 328"; under it a "While you
   wait" card that shows one random topic from `content/learning.json`: its `title` and its
   `short` line (both via textContent; skip if learning.json has not loaded). Fade the
   overlay out over 400ms when loading finishes, then remove it. If loading fails, keep the
   existing failure UI visible (hide the loader).

6. **Start links** (read once after `learning.json` and the models have loaded):
   - `?level=beginner|some|expert` → set `learnerProfile.level` to it, set `onboarded =
     true`, save the profile, and apply the level the same way the onboarding buttons do.
   - `?start=tour` → start the `brain-101` tour (same call the onboarding "Start Brain 101"
     button makes).
   - `?start=quiz` → switch to the Quiz tab and start the Quick 10 session (same handler as
     `#qcard-quick`).
   - `?start=explore` or no parameter → current behaviour.
   Accept only these exact values; ignore anything else. Do not break `#hash` deep links.

7. **Quiz streak**: in the quiz HUD, show "🔥 N in a row" (small, `--amber`) once the
   learner has 3 or more correct answers in a row in the current session; reset on a wrong
   answer. On each correct answer, give the HUD a 600ms green glow pulse (none with reduced
   motion).

## Report

After each part, list what you changed with line numbers. Do not run the app; Claude tests
in the browser on desktop and phone.

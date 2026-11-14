# Tier 6 polish: neuron mode and imaging page

Two new pages exist and work: `viewer/public/neuron.html` and `viewer/public/imaging.html`.
Read `docs/tasks/tier6-common.md` first: its hard rules apply (no external requests, keep the
CSP, never `innerHTML` with data, no neuroscience facts written by you, reduced motion,
phones at 360 px, no uppercase styling). Make targeted edits only. Do not touch
`atlas-viewer.html`, `index.html` or any file in `viewer/public/content/`.

Do the items in order. After each one, say what you changed in one or two lines.

## A. `viewer/public/neuron.html`

1. **Labels overlap after rotating.** With "Labels" on, the leader-line labels use fixed
   offsets and can sit on top of each other. After projecting the label positions each frame,
   sort them by screen y and push any label that overlaps the one above it down by the
   overlap plus 4 px (one pass is enough). Keep the leader line pointing at the part. Hide a
   label whose anchor is off-screen.
2. **Dendritic spines are hard to click.** Add an invisible, larger hit target for the
   spines (for example a transparent sphere about 3x the spine radius per instance, or one
   merged invisible mesh) that the raycaster treats as `dendritic_spines`. The visible
   geometry must not change. Other parts in front must still win the pick.
3. **Phone: the synapse close-up hides the 3D view.** Below 760 px, cap the close-up at
   about 46% of the viewport height, make its diagram scale to fit, and add a
   "Hide / Show diagram" button so the learner can get the neuron back without closing the
   step text.
4. **Find-the-part quiz feedback.** After a wrong click, briefly outline the part the
   learner clicked (0.6 s, no animation under reduced motion) and name it in the feedback
   line: "That is the <part name>. Try again." Part names come from `content/neuron.json`.

## B. `viewer/public/imaging.html`

5. **Source markers are narrow tap targets on phones.** Keep them looking the same, but
   give each a hit area of at least 44 x 44 px below 760 px (padding or a `::after` hit
   area), without neighbouring markers overlapping; add a little spacing if needed.
6. **The resolution table is long on phones.** Below 600 px, render each method as a
   stacked card (method name as the heading, then "Finest detail", "Finest timing", and the
   plain-words line) instead of a four-column table. Keep the real `<table>` for wider
   screens and for screen readers (or use proper headings in the cards).

## Checks

- Open both pages at 1280x800 and 390x844 and in reduced-motion mode. No console errors.
- `python3 scripts/tests/test_neuron.py` and `python3 scripts/tests/test_imaging.py` exist;
  run them if Chrome is available, and do not weaken a check to make it pass.
- Report what you verified and anything you could not verify.

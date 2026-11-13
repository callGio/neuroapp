# Tier 6A: neuron mode (`viewer/public/neuron.html`)

Read `tier6-common.md` first. It holds the rules, design system and required checks.

Goal: the learner leaves the whole brain and lands on a single neuron they can turn, click
and watch work. Same learning loop as the atlas: look, click a part, read what it does at
your level, see it act, test yourself.

## Content file: `viewer/public/content/neuron.json`

```json
{
  "version": 1,
  "note": "Paraphrased from the cited sources. Educational use only; not medical advice.",
  "sources": { "<id>": { "citation": "APA 7", "url": "https://…", "license": "CC BY 4.0" } },
  "scale": { "text": "one or two sentences on how small a neuron is next to the brain", "cite": [] },
  "intro": { "beginner": "2 sentences", "expert": "2 sentences", "cite": [] },
  "parts": [
    {
      "id": "soma", "name": "Cell body (soma)", "short": "one line under 90 characters",
      "analogy": "optional plain-language comparison, flagged as an analogy in the UI",
      "levels": {
        "beginner": { "summary": "…", "points": [ { "text": "…", "cite": ["id"] } ] },
        "expert":   { "summary": "…", "points": [ { "text": "…", "cite": ["id"] } ], "caveat": "optional" }
      },
      "related": ["axon_hillock"]
    }
  ],
  "processes": [
    {
      "id": "action-potential", "title": "How a neuron fires",
      "summary": { "beginner": "…", "expert": "…" },
      "steps": [ { "key": "rest", "title": "At rest", "text": { "beginner": "…", "expert": "…" }, "cite": [] } ]
    }
  ],
  "compare": {
    "intro": "…", "cite": [],
    "rows": [ { "bio": "Dendrites receive signals", "ann": "Inputs x1…xn", "note": "…" } ],
    "caveats": [ { "text": "…", "cite": [] } ]
  },
  "quiz": [ { "type": "function", "q": "…", "options": ["…"], "answer": 0, "explain": "…", "cite": [] } ],
  "glossary": [ { "term": "…", "definition": "…", "cite": [] } ]
}
```

Part ids (fixed; the 3D meshes use these names): `soma`, `nucleus`, `dendrites`,
`dendritic_spines`, `axon_hillock`, `axon`, `myelin_sheath`, `node_of_ranvier`,
`axon_terminals`, `synapse`. Mention glia (Schwann cells, oligodendrocytes) inside
`myelin_sheath`. Beginner: 2–4 short points per part. Expert: 3–5 points with the
mechanism (ion channels, organelles, proteins) as far as the sources support.

Processes (fixed ids and step keys; the animation is driven by `key`):

- `resting`: `rest` (what resting potential is, which ions sit where).
- `action-potential`: `rest`, `threshold`, `depolarization`, `repolarization`,
  `hyperpolarization`, `return` (refractory period belongs in the expert text).
- `conduction`: `continuous`, `saltatory` (why myelin makes signals faster).
- `synapse`: `arrive`, `calcium`, `release`, `bind`, `clear`.
- `summation`: `epsp`, `ipsp`, `threshold` (inputs add up at the axon hillock; all-or-none).

Starting sources (verify, add others that meet the rules): OpenStax *Anatomy and Physiology
2e* sections 12.2 Nervous Tissue, 12.4 The Action Potential, 12.5 Communication Between
Neurons; OpenStax *Biology 2e* 35.1 and 35.2; OpenStax *Psychology 2e* 3.2. For the
artificial-neuron comparison use a primary or textbook source (for example McCulloch & Pitts,
1943; Rosenblatt, 1958; or an open ML textbook) and state plainly that an artificial neuron
is a loose mathematical abstraction, not a model of how real neurons compute.

At least 12 quiz items: about half `"type":"function"` (multiple choice from the content) and
the page also generates "find the part" questions from `parts` on its own.

## Page layout

Desktop: 3D canvas fills the page; a glass panel on the right (about 400 px) like the
viewer's. Phone: canvas on top, panel as the lower sheet.

Panel tabs (real tabs, arrow-key navigable):

1. **Explore**: list of the ten parts (name + `short`). Clicking a part in the list or on
   the model selects it: the camera eases to frame that part, the part glows, the others
   dim, and the panel shows the focus view: name, analogy (labelled "Analogy"), summary,
   points with source markers, "Related parts" chips, and a "See it in action" button when a
   process involves that part (it switches to tab 2 at the right process).
2. **How it works**: the five processes as a short list. Opening one shows a stepper
   (Back / Next, step dots, optional Play) with the step text for the current level, while
   the 3D scene and the voltage trace act out the step (see Animation).
3. **Compare**: biological neuron beside artificial neuron (see Compare tab).
4. **Quiz**: one question at a time, score and streak, friendly feedback with the `explain`
   text. "Find the part" questions ask the learner to click the part on the model; give a
   "Show me" after a wrong try.

Top of the panel: level switch (Beginner / Expert) and a search field that filters parts and
glossary terms. A "Labels" toggle shows leader-line labels on the model (HTML overlay
positioned from projected 3D points; hide labels of parts behind the camera).

## The 3D neuron (procedural, three.js, no model files)

A stylised multipolar neuron, built in code so each part is its own mesh/group named by part
id. It must read instantly as a neuron from the default camera angle: soma on the left,
dendritic tree fanning up/left, a long axon running right, terminals at the far right
touching the dendrite of a second, fainter neuron (only its receiving dendrite and part of
its soma, to show where the signal goes next).

- `soma`: slightly irregular sphere (displace vertices with smooth noise), translucent
  enough to hint at the nucleus; a "Look inside" toggle fades the membrane to show
  `nucleus` (inner sphere with a darker nucleolus).
- `dendrites`: 5–7 trunks from the soma, each branching 2–3 times, tapered tubes
  (`TubeGeometry` along Catmull-Rom curves, radius shrinking per branch level), gentle curves,
  seeded random so it is the same every load.
- `dendritic_spines`: small knobs along the outer dendrites (instanced). Because they are
  tiny, selecting them moves the camera close to one branch.
- `axon_hillock`: a short cone where the axon leaves the soma, visibly distinct.
- `axon`: one long, thin, slightly wavy tube.
- `myelin_sheath`: 6–8 rounded segments wrapped around the axon, lighter colour.
- `node_of_ranvier`: the exposed gaps between segments; make them selectable (thin ring
  hit-areas) and highlight all nodes together.
- `axon_terminals`: the axon splits into 4–6 short branches ending in boutons.
- `synapse`: the junction between one bouton and the second neuron's dendrite; selecting it
  opens the synapse close-up.

Colours: parts use the palette tokens (soma/dendrites violet family, axon cyan family, myelin
pale, terminals pink, second neuron muted). Lighting: soft hemisphere + one key light; subtle
rim/fresnel so it feels alive, slow idle rotation that stops on interaction and never runs
under reduced motion. OrbitControls with damping, sensible min/max distance, a "Reset view"
button. Picking: raycast on pointer up with the same tap-slop idea as the viewer (ignore if
the pointer moved more than ~6 px mouse / 10 px touch). Hover shows the part name on desktop.

## Animation ("How it works")

- **Voltage trace**: a small canvas plot under/over the stepper: membrane potential (mV)
  against time, with labelled resting, threshold and peak lines. The values and labels come
  from the content JSON (put them in the process object, with a cite). The trace draws in
  step with the stepper and marks the current phase. Label the plot "Illustration".
- **Action potential**: a glowing pulse travels from the axon hillock down the axon to the
  terminals. With myelin on, the glow jumps node to node; a "Remove myelin" switch shows the
  slower continuous version side by side in time (same distance, visibly longer). Do not
  print speeds unless the JSON gives cited numbers.
- **Synapse close-up**: when the pulse arrives, or when `synapse` is selected, show a
  close-up diagram: presynaptic terminal with vesicles, the cleft, receptors on the
  postsynaptic membrane. Steps: signal arrives, calcium enters, vesicles fuse and release
  neurotransmitter, molecules cross and bind receptors, neurotransmitter is cleared. A 2D
  SVG/canvas panel overlaid on the scene is fine and usually clearer than 3D. Each visible
  element is labelled.
- **Summation playground**: two buttons, "Excitatory input" and "Inhibitory input". Each
  press nudges the trace up or down from rest and the bump decays; if pushes arrive close
  enough together to cross threshold, the neuron fires the full action-potential animation,
  the same size every time. A one-line readout says what happened ("Below threshold: no
  signal sent"). This is the one place a learner discovers all-or-none by playing.

All animations have Play/Pause and step controls; under reduced motion they are step-only.

## Compare tab (biological and artificial neuron)

Left: a small schematic of the neuron's parts. Right: a perceptron diagram (two inputs,
weights, sum, threshold, output). Rows from `compare.rows` link the two sides: hovering or
focusing a row highlights both. Below: sliders for two inputs and two weights and a
threshold; the output node lights when the weighted sum crosses the threshold, and the sum is
shown as a number. Then the caveats from the JSON, prominently: this is a simplification that
inspired artificial networks, not a description of how real neurons compute.

## Arrival

On first load (and when the URL has `?from=atlas`), a 3-second intro overlay: the brain
image `./assets/brain-lateral.webp` shrinks toward a point while the neuron fades in, with
the `scale.text` line and its source marker. "Skip" button; never shown under reduced motion
(show the scale line as a dismissible note instead); shown once per browser otherwise
(`localStorage`, try/catch).

Deep links: `?part=<id>`, `?process=<id>`, `?tab=quiz`, `?level=beginner|expert`.

## Done when

The checks in `tier6-common.md` pass, the screenshots look like a neuron a textbook would
print, and a beginner can answer "what does myelin do?" after two minutes on the page.

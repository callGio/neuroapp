# Tier 6B: brain-imaging page (`viewer/public/imaging.html`)

Read `tier6-common.md` first. It holds the rules, design system and required checks.

Goal: a learner who has heard "fMRI" and "EEG" but could not say what either measures
leaves able to say what each method records, what it is good for, what it cannot tell you,
and which one fits a given question.

No 3D on this page. Use inline SVG and small canvases. No real scan images: every picture is
a drawn schematic labelled "Illustration, not a real scan".

## Content file: `viewer/public/content/imaging.json`

```json
{
  "version": 1,
  "note": "Paraphrased from the cited sources. Educational use only; not medical advice.",
  "sources": { "<id>": { "citation": "APA 7", "url": "https://…", "license": "…" } },
  "intro": { "beginner": "…", "expert": "…", "cite": [] },
  "families": [ { "id": "structure", "title": "Pictures of structure", "text": "…", "cite": [] } ],
  "methods": [
    {
      "id": "fmri", "name": "fMRI", "full": "Functional magnetic resonance imaging",
      "family": "activity", "short": "one line under 90 characters",
      "measures": { "text": "what physical signal it records", "cite": [] },
      "direct": false,
      "levels": {
        "beginner": { "summary": "…", "points": [ { "text": "…", "cite": [] } ] },
        "expert":   { "summary": "…", "points": [ { "text": "…", "cite": [] } ], "caveat": "…" }
      },
      "good_for": [ { "text": "…", "cite": [] } ],
      "limits":   [ { "text": "…", "cite": [] } ],
      "experience": { "text": "what it is like for the person being scanned", "cite": [] },
      "resolution": {
        "spatial_mm": [1, 3], "temporal_s": [1, 3], "approximate": true,
        "text": "plain-language version of the same ranges", "cite": []
      },
      "invasive": "none | injection | surgery",
      "misconception": { "claim": "a common wrong idea", "correction": "…", "cite": [] }
    }
  ],
  "eeg": {
    "system": { "text": "what the 10–20 system is and how electrodes are named", "cite": [] },
    "letters": [ { "letter": "F", "meaning": "frontal", "cite": [] } ],
    "electrodes": [ { "id": "Fp1", "x": 0.0, "y": 0.0, "region": "left frontal pole" } ],
    "bands": [ { "id": "alpha", "name": "Alpha", "hz": [8, 13], "text": "…", "cite": [] } ],
    "depth": { "text": "why scalp EEG sees cortex better than deep structures", "cite": [] }
  },
  "chooser": [
    { "q": "a research question in plain words", "options": ["eeg","fmri","mri","pet"],
      "answer": "eeg", "explain": "…", "cite": [] }
  ],
  "glossary": [ { "term": "…", "definition": "…", "cite": [] } ]
}
```

Methods, in this order: `mri` (structural), `dti` (diffusion imaging of white matter), `ct`
(brief, for contrast with MRI), `fmri`, `pet`, `eeg`, `meg`. For each, the sources must
support: the signal measured, whether it measures neural activity directly or through a
proxy (blood flow, metabolism), rough spatial and temporal resolution, what it costs the
participant (noise, stillness, radiation, injection), and one honest limit. Required points:

- MRI shows anatomy, not activity. fMRI's BOLD signal follows blood oxygenation, which lags
  neural activity by seconds; it is an indirect measure.
- An fMRI "activation" is a statistical difference between conditions, not a region
  "switching on"; and a region being active does not by itself tell you which mental process
  is occurring (reverse inference; Poldrack, 2006, is the standard reference).
- EEG and MEG record electrical/magnetic fields from many neurons acting together, with
  millisecond timing and weaker localisation; why MEG needs shielding and special sensors.
- PET and CT involve ionising radiation; MRI does not, but has magnet-safety limits.

Resolution numbers: take ranges from a citable source (for example Sejnowski, Churchland &
Movshon, 2014, *Nature Neuroscience*, or a methods textbook/review). If sources disagree,
use the wider range and set `"approximate": true`. Never invent a number.

Starting sources (verify, add others that meet the rules): OpenStax *Psychology 2e* 3.4
(brain-imaging section), NIBIB/NIH pages on MRI, CT and nuclear medicine/PET, NINDS/NIMH
pages, StatPearls chapters on EEG and on the 10–20 system, Poldrack (2006), Logothetis
(2008), Sejnowski et al. (2014), Hämäläinen et al. (1993) or a later open MEG review.

EEG electrodes: the standard 19 scalp positions of the 10–20 system plus the two ear
references, with x/y in a unit circle (nose up). Bands: delta, theta, alpha, beta, gamma
with the frequency ranges the source gives (ranges differ slightly between sources; cite the
one used and say "about").

`chooser`: at least 8 scenarios, each with one best answer and an explanation that names the
trade-off (timing against location, structure against activity, risk against benefit).

## Page sections

1. **Opening**: one heading, two sentences (`intro` at the current level), the level
   switch, and a row of method chips that jump to each method.
2. **Two questions, two families**: a short visual split: "What does the brain look like?"
   (MRI, DTI, CT) and "What is the brain doing?" (fMRI, PET, EEG, MEG), text from `families`.
3. **The trade-off chart** (the centrepiece): an SVG chart with time on the x-axis
   (log scale from milliseconds to minutes; plain labels such as "a thousandth of a second")
   and space on the y-axis (log scale from about a millimetre to several centimetres). Each
   method is a rounded rectangle spanning its cited ranges. Selecting a method (click, tap or
   keyboard) highlights it and shows its `resolution.text`. A one-line caption states the
   lesson and that ranges are approximate. Include a text table of the same data for screen
   readers and narrow phones. Structural methods (MRI, DTI, CT) take a single picture, so
   draw them along the space axis only, in a separate strip labelled "still pictures".
4. **Method cards**: one section per method: name, full name, a drawn schematic of the
   machine/setup (simple, consistent line style, inline SVG), "What it measures" with a
   Direct / Indirect tag, summary and points for the level, "Good for", "Limits", "What it is
   like", and the misconception as a small "Common mix-up" block. Collapsible on phones.
5. **EEG explorer**: left: a top-view head (nose up, ears) with the electrodes as buttons;
   selecting one shows its name decoded ("F = frontal, 3 = left side") and the region under
   it. Right: a rhythm viewer: pick a band and a canvas draws a synthetic wave at a frequency
   inside that band, labelled "Synthetic signal for illustration", with the band's text. No
   autoplay under reduced motion (draw a static trace). Then the `depth` note.
6. **Which tool would you use?**: the `chooser` quiz, one scenario at a time, method
   buttons as answers, feedback with the explanation, score at the end, "Try again".
7. **Glossary and sources**.

Links to the rest of the app: where a card mentions a structure the atlas has, no deep
linking is required; one closing line with buttons "Explore the whole brain" and "Look
inside a neuron" is enough.

## Done when

The checks in `tier6-common.md` pass, the chart is readable on a 390 px phone, and a beginner
can answer "why can't EEG tell you exactly where a signal came from, and why can't fMRI tell
you exactly when?" after reading the page.

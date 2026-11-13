# NeuroApp — learn the human brain in 3D

NeuroApp is a free, offline, browser-based 3D brain atlas for **learning** neuroanatomy.
Rotate a whole human brain built from 328 real anatomical structures, click any part to
see what it is and how it connects, take guided tours, and quiz yourself with spaced
review that adapts to what you know.

It is designed for two kinds of learners at once:

- **Complete beginners.** Start with a short welcome, a "Brain 101" tour, plain-language
  summaries, and a glossary that explains terms like *anterior* or *gyrus* when you hover them.
- **Experts.** Switch to expert depth: subfields, pathways, Brodmann areas, clinical notes,
  and the full 328-structure quiz pool.

Every factual statement in the lessons cites an open, checkable source.

**Live demo:** https://giovannicallahan.github.io/neuroapp/ (works in any modern desktop browser;
the first load downloads about 55 MB of 3D models).

> Educational use only. Not medical advice. The underlying atlas is not FDA-reviewed and
> is not intended for clinical use.

## Features

**Explore**
- Click or search any of 328 structures; the camera frames it and a breadcrumb shows where
  it sits (Brain › prosencephalon › telencephalon › … › left hippocampus).
- Standard anatomical views (anterior, posterior, left, right, superior, inferior) and an
  orientation compass.
- Sagittal, coronal and axial cutting planes; left/right/midline hemisphere toggles;
  isolate a structure or a whole group such as a lobe.
- Shareable deep links, e.g. `atlas-viewer.html#left_hippocampus`, plus start links:
  `?start=tour` opens the Brain 101 tour, `?start=quiz` starts a quick quiz, and
  `?level=beginner|some|expert` sets the lesson depth.

**Learn**
- Lessons at beginner or expert depth, each point with numbered citations.
- Clickable connections (for example, hippocampus → fornix → anterior thalamus).
- Glossary tooltips and guided tours that ask you to *predict* before they explain.
- Pathway tours that trace a signal through the atlas: seeing, hearing and touch.
- **Neuron mode** (`neuron.html`): a clickable 3D neuron with every part explained at two
  levels, step-by-step animations of the action potential, myelin and the synapse, an
  input-summation playground, a comparison with an artificial neuron, and a quiz.
- **Brain-imaging guide** (`imaging.html`): what MRI, DTI, CT, fMRI, PET, EEG and MEG
  measure, a time-against-space trade-off chart, an EEG electrode and rhythm explorer, and
  a "which tool would you use?" quiz.

**Practice**
- *Find it*: the app names a structure, you click it on the brain.
- *Name it*: the app highlights a structure, you pick its name. Distractors include the
  same structure on the other side, so you learn laterality.
- *Function* questions drawn from the cited lessons.
- Spaced review (Leitner boxes: same session, 1, 3, 7, 21 days) with confidence ratings;
  confident mistakes are re-taught immediately.
- A mastery map colors the brain by how well you know each part.

**Works on phones**
- On screens up to 760 px wide the panel becomes a bottom sheet: drag or tap its handle to
  show just the tabs, half the screen, or nearly all of it.
- One finger rotates, two fingers pinch to zoom, a tap selects; the brain re-centres in the
  space above the sheet, and quiz questions sit below the brain so it stays visible.

## Why it works this way

The practice design follows two well-replicated findings: retrieving information beats
re-reading it, and spacing practice over time beats cramming. In anatomy specifically,
distributed retrieval practice produced the best recall in Dobson, Perez, and Linderholm
(2017). NeuroApp therefore teaches a structure first, then asks you to retrieve it, then
brings it back at growing intervals.

Dobson, J. L., Perez, J., & Linderholm, T. (2017). Distributed retrieval practice promotes
superior recall of anatomy information. *Anatomical Sciences Education, 10*(4), 339–347.
https://doi.org/10.1002/ase.1668

## Quick start

You need Python 3 (already on macOS and most Linux systems). No accounts, no API keys,
nothing to install.

```bash
git clone https://github.com/giovannicallahan/neuroapp.git
cd neuroapp/viewer/public
python3 -m http.server 8080 --bind 127.0.0.1
```

Then open http://127.0.0.1:8080/ in Chrome, Edge, Firefox or Safari. The welcome page links into the
atlas; you can also open http://127.0.0.1:8080/atlas-viewer.html directly.
(Opening the HTML file directly from disk will not work; browsers block loading the 3D
models from `file://`.)

Your learning progress is stored only in your own browser (`localStorage`).

## Rebuilding the 3D models (optional)

The converted models are already in `viewer/public/models/`. To regenerate them:

1. Download the atlas: https://www.openanatomy.org/atlases/nac/brain-2017-01.zip and unzip
   it into the repository root as `brain-2017-01/`.
2. `pip install vtk`
3. `python3 scripts/convert_atlas.py`

The converter accounts for every source file (exported, byte-identical duplicate, curve,
unmapped, or failed), keeps the atlas's original coordinates, and writes
`viewer/public/atlas-manifest.json`.

## Project layout

```
scripts/convert_atlas.py         VTK -> glTF converter and manifest builder
scripts/check_atlas_samples.py   3-mesh sanity check (shared reader/writer)
viewer/public/index.html         the welcome page
viewer/public/neuron.html        neuron mode (content/neuron.json)
viewer/public/imaging.html       brain-imaging guide (content/imaging.json)
viewer/public/atlas-viewer.html  the app (Three.js, no build step)
viewer/public/atlas-manifest.json  structure names, hierarchy, colors, RadLex IDs
viewer/public/models/            328 binary glTF meshes
viewer/public/content/learning.json  cited lessons, glossary, tours, questions
viewer/public/vendor/three/      pinned, checksum-verified three.js r160
docs/tasks/                      the build specifications used during development
```

## Content and accuracy

`content/learning.json` is a **pilot**: 62 topics, 20 glossary terms and 6 tours, each
statement paraphrased from and cited to OpenStax or StatPearls. Content should be checked
against its sources before being marked reviewed. Corrections are welcome as issues.

## Security and privacy

- Runs entirely on your machine; no network calls except loading its own files.
- three.js is vendored and pinned by checksum instead of loaded from a CDN.
- All text from data files is escaped before display; a Content Security Policy limits
  what the page may load.
- No analytics, cookies, accounts or personal data.

## Deploying the demo

The demo is served by GitHub Pages from the `gh-pages` branch, which holds only the
contents of `viewer/public/`. After changing the app on `main`, publish it with:

```bash
git subtree split --prefix viewer/public -b gh-pages-tmp
git push -f origin gh-pages-tmp:gh-pages
git branch -D gh-pages-tmp
```

## License

The code and lesson text written for this project are released under the
[MIT License](LICENSE). Third-party material keeps its own license: the 3D models
and manifest derived from the SPL/NAC Brain Atlas are under the 3D Slicer license,
three.js is MIT, and cited works remain under their publishers' terms. See
[NOTICE.md](NOTICE.md).

## Credits

- 3D anatomy: SPL/NAC Multi-modality MRI-based Atlas of the Brain (Halle et al., 2017),
  Surgical Planning Laboratory, Brigham and Women's Hospital, under the 3D Slicer license.
  See [NOTICE.md](NOTICE.md).
- Rendering: [three.js](https://threejs.org) (MIT).
- Lesson sources: OpenStax (CC BY 4.0) and StatPearls (NCBI Bookshelf).

Built by Giovanni Callahan.

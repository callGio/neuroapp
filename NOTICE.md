# Notices and third-party attribution

The MIT License in `LICENSE` covers only material written for this project
(the scripts, the viewer pages, and the lesson text in
`viewer/public/content/learning.json`). Third-party material below keeps its own license.

NeuroApp bundles or derives from the following third-party material. Each keeps its own license.

## SPL/NAC Brain Atlas (3D models)

`viewer/public/models/*.glb`, `viewer/public/models_sample/*.glb` and
`viewer/public/atlas-manifest.json` are **modified versions** derived from the
SPL/NAC Multi-modality MRI-based Atlas of the Brain, release `brain-2017-01`.

> All or portions of this licensed product (such portions are the "Software") have been obtained under license from The Brigham and Women's Hospital, Inc. and are subject to the following terms and conditions:
> see [`third_party/spl-brain-atlas/SLICER-LICENSE.txt`](third_party/spl-brain-atlas/SLICER-LICENSE.txt).

Modifications made by this project (`scripts/convert_atlas.py`):

- Surface meshes (`.vtk`, binary legacy format) were triangulated and re-encoded as binary glTF 2.0 (`.glb`). Vertex coordinates are unchanged (RAS atlas space).
- 31 source files that are byte-identical copies of other files were not converted.
- Structure names, colors, group hierarchy and RadLex IDs were copied into `atlas-manifest.json` from the atlas's `atlasStructure.json` and label table.

Citation: Halle, M., Talos, I.-F., Jakab, M., Makris, N., Meier, D., Wald, L. L., Fischl, B., & Kikinis, R. (2017). *Multi-modality MRI-based atlas of the brain* [Data set]. Surgical Planning Laboratory, Brigham and Women's Hospital. http://www.spl.harvard.edu/publications/item/view/1265

The atlas was developed with support from the National Institutes of Health under grants P41 EB015902/RR/NIBIB (Neuroimage Analysis Center), P41 RR013218/RR/NCRR and R01 MH050740/MH/NIMH, and a Google Research Grant.

**The atlas is for research and education. It is not FDA-reviewed, and clinical use is neither recommended nor advised.** No endorsement by Brigham and Women's Hospital or the atlas contributors is implied.

Original download: https://www.openanatomy.org/atlases/nac/brain-2017-01.zip (not included in this repository).

## three.js

`viewer/public/vendor/three/` contains unmodified files from three.js r160 (npm `three@0.160.1`,
integrity `sha512-Bgl2wPJypDOZ1stAxwfWAcJ0WQf7QzlptsxkjYiURPz+n5k4RBDLsq+6f9Y75TYxn6aHLcWz+JNmwTOXWrQTBQ==`),
MIT License, copyright 2010-2023 three.js authors. See `viewer/public/vendor/three/LICENSE`.

## Learning content sources

`viewer/public/content/learning.json` contains original summaries written for this project.
Each statement cites its source. Sources include OpenStax *Anatomy and Physiology 2e* and
*Introduction to Behavioral Neuroscience* (CC BY 4.0; access for free at https://openstax.org)
and StatPearls chapters on the NCBI Bookshelf. No source text is reproduced beyond short terms.
The content is educational and is not medical advice.

# Task: Tier 1 — navigation and orientation (atlas-viewer.html)

Edit ONLY `viewer/public/atlas-viewer.html`. Do not touch scripts/, atlas-manifest.json,
models/, models_sample/, sample-preview.html, or brain-2017-01/. No new dependencies,
no build step, keep the existing three@0.160.1 import map. Do not add anatomical facts
(function, connections, clinical notes); Function/Connections stay as placeholders.

Note: line ~707 `showInfoPanel` now sets `info-content` display to 'block' (a CSS rule
hides it by default). Keep that fix.

## Known bug to fix first
Camera framing on selection is wrong. `selectModel()` builds the box with
`new THREE.Box3().setFromObject(entry.mesh)`, which is ALREADY in world space.
`fitBox()` then applies `group.matrixWorld` again, so the RAS->Three rotation is
applied twice and the camera aims at the wrong place. Pass the world box straight to
`applyCameraToBox()`. Also: when framing, keep the current viewing direction
(move the camera along its existing view vector) instead of snapping to +Z.

## Features (do them in this order; each must work before the next)
1. Camera framing fix (above). Selecting a structure frames it so it fills ~60% of view.
2. Hover label: a small tooltip with the structure name follows the cursor when hovering
   a visible mesh. Throttle raycasts (e.g. once per animation frame).
3. View presets: buttons Anterior, Posterior, Left, Right, Superior, Inferior. Use RAS
   anatomy: +X = right, +Y = anterior, +Z = superior (before the group's -90° X rotation).
   "Left" view = camera on the subject's left looking right. Animate ~400 ms.
4. Orientation gizmo: small corner compass showing A/P, S/I, L/R that rotates with the camera.
5. Cutting planes: three sliders (Sagittal, Coronal, Axial) using renderer.localClippingEnabled
   and material.clippingPlanes on all brain materials; each slider has an on/off checkbox
   and a flip-side toggle. Range = manifest bounds. Use material.side = DoubleSide so cut
   surfaces show the interior.
6. Hemisphere toggles: Left / Right / Midline checkboxes using model.hemisphere
   (null = midline/unlateralized).
7. Context opacity slider: controls how transparent non-selected structures are while
   something is selected (currently fixed dim value).
8. Breadcrumb in the info panel: Brain > ... > parent group > structure, built from
   manifest.groups. Clicking a group name selects the whole group (highlight + frame all
   its models), and the info panel shows the group name and its member count.
9. Deep links: selecting a structure updates location.hash to its atlas_id
   (e.g. #left_hippocampus); loading the page with a hash selects it after meshes load.
10. Keyboard: `/` focuses search, Esc deselects, I isolates, A shows all,
    1–6 the six view presets, ? shows a small shortcuts overlay.

## Definition of done (report each item)
- No console errors; "All 328 meshes loaded".
- For each feature 1–10: what you did and how you tested it.
- Specifically: select "left hippocampus" -> it is centered and fills a good part of view.
- File list: only viewer/public/atlas-viewer.html changed.
Stop after this task. Do not start quizzes or content.

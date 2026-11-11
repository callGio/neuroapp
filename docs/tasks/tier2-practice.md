# Task: Tier 2 — practice modes (atlas-viewer.html)

Context: NeuroApp is a local 3D brain-learning viewer. `viewer/public/atlas-viewer.html`
(Three.js 0.160.1 via import map) loads `viewer/public/atlas-manifest.json`
(models[] with id, name, hemisphere, glb, structures[{atlas_id, parent_groups...}];
groups[] with id, name, members; roots). Tier 1 navigation is done and tested:
selection, framing, view presets, gizmo, cutting planes, hemisphere toggles,
breadcrumb, deep links, keyboard shortcuts.

Rules: edit ONLY `viewer/public/atlas-viewer.html`. No new dependencies, no build step.
Do not change the manifest, scripts/, models/, or brain-2017-01/. Do not add anatomical
facts; quizzes use only names and hierarchy from the manifest. Do not break Tier 1.
Do not use alert/confirm/prompt dialogs; use inline UI.
Orientation reminder: group.rotation.x = -PI/2 maps RAS +Z (superior) to world +Y and
RAS +Y (anterior) to world -Z; RAS +X is the subject's right. Use transformDirection.

## Why
Retrieval practice spaced over time produces better anatomy recall than re-studying
(Dobson, Perez & Linderholm, 2017, Anat Sci Educ 10:339-347). So the app should make
the learner retrieve names and locations, spaced and interleaved.

## Features (in order)
1. Mode switch at the top of the side panel: Explore | Quiz. Explore = current behavior.
2. Quiz setup: scope = "All brain structures" or the current group-filter selection;
   skin and head/neck muscles excluded unless the Muscles toggle is on; question type =
   Find it / Name it / Mixed; session length 10 / 20 / 30.
3. Find it: show a structure name; learner clicks a mesh. While quizzing, the hover
   tooltip, info panel, breadcrumb and search are hidden (they would give the answer).
   Correct -> brief green highlight. Wrong -> clicked mesh red, correct mesh green and
   framed, both names shown; "Next" (Enter) continues.
4. Name it: highlight and frame the target (others at context opacity); show 4 options.
   Distractors: prefer the contralateral counterpart (left <-> right same name) and
   siblings from the same parent group; fall back to random brain structures. Keys 1-4
   answer, Enter continues.
5. Spaced review (Leitner): boxes 1-5 with review intervals 0 (same session), 1, 3, 7,
   21 days. Correct -> box+1 (max 5); wrong -> box 1. Session queue: due items first,
   then at most 10 new items, shuffled (interleaved across regions). Store per model id
   {box, due, seen, correct} in localStorage key "neuroapp.srs.v1" (wrap all access in
   try/catch; if unavailable, keep state in memory and say so in the UI).
6. Session summary: accuracy, list of missed structures (click one -> Explore mode with
   it selected), and "Review missed now".
7. Mastery map toggle (in Explore): color each structure by box (unseen gray,
   box 1 red ... box 5 green) with a small legend; toggling off restores colors.
8. Progress panel: counts per box, number due today, "Reset progress" with an inline
   confirm step.

## Definition of done (report each item)
- List what you changed per feature. Do not claim browser tests you did not run;
  Claude will test in the browser.
- Only viewer/public/atlas-viewer.html changed.
Stop after this task.

# Task: Tier 3 — adaptive learning layer (atlas-viewer.html)

Context: `viewer/public/atlas-viewer.html` already has Explore (Tier 1: selection,
framing, presets, gizmo, cutting planes, hemisphere toggles, breadcrumb, deep links,
shortcuts) and Quiz (Tier 2: Find it / Name it, Leitner spaced review in localStorage
"neuroapp.srs.v1", summary, mastery map, progress panel). Both are tested and working.

Rules: edit `viewer/public/atlas-viewer.html` only. Read content from
`viewer/public/content/learning.json` (schema below; Claude writes this file — do not
write anatomical facts yourself, and never invent citations). No new dependencies, no
build step, no alert/confirm/prompt. Declare every const/let before the render loop or
any handler uses it. Escape every string from JSON before inserting into the DOM
(use textContent or the existing escHtml; never innerHTML with raw JSON text).
Make targeted edits, not a whole-file rewrite.

## content/learning.json schema
{
  "version": 1,
  "sources": { "<srcId>": { "citation": "APA 7 reference", "url": "https://...", "license": "..." } },
  "glossary": [ { "term": "anterior", "definition": "...", "cite": ["<srcId>"] } ],
  "topics": [ {
      "id": "hippocampus", "title": "Hippocampus",
      "applies_to": { "atlas_ids": ["left_hippocampus","right_hippocampus"], "groups": [] },
      "core": true,                       // part of the beginner core set
      "levels": {
        "beginner": { "summary": "...", "points": [ { "text": "...", "cite": ["<srcId>"] } ] },
        "expert":   { "summary": "...", "points": [ { "text": "...", "cite": ["<srcId>"] } ] }
      },
      "connections": [ { "atlas_ids": ["left_fornix_of_forebrain"], "label": "...", "cite": ["<srcId>"] } ],
      "clinical":    [ { "text": "...", "cite": ["<srcId>"] } ],
      "checks": [ { "level": "beginner", "q": "...", "options": ["..","..",".."], "answer": 0,
                   "explain": "...", "cite": ["<srcId>"] } ]
  } ],
  "tours": [ { "id": "brain-101", "title": "...", "level": "beginner",
      "steps": [ { "atlas_ids": [...], "groups": [...], "view": "left", "predict": "optional question shown before reveal",
                   "text": "...", "cite": ["<srcId>"] } ] } ]
}
A topic matches a selected model if the model's atlas_id is in applies_to.atlas_ids or the
model belongs (recursively) to any group in applies_to.groups. Group-level topics also show
when that group is selected via the breadcrumb.

## Features (in order)
1. Learner profile + onboarding. On first visit show an inline welcome card (not a dialog):
   "How familiar are you with neuroscience?" -> New to it / Some background / Expert.
   Store in localStorage "neuroapp.profile.v1" {level, onboarded, seen:{topicId:true}}
   (try/catch, in-memory fallback). A level switch stays visible in the side panel.
   New-to-it users get a one-screen orientation: how to rotate/zoom/select, and a button
   "Start the Brain 101 tour".
2. Learn panel in the info panel: for the selected structure show the matching topic at
   the user's level (beginner summary+points; expert shows expert, with a "simpler" toggle;
   "some background" shows beginner + expert points collapsed). Each point shows numbered
   citation markers; a "Sources" list at the bottom renders citation text + link
   (target=_blank rel="noopener noreferrer"). Connections render as clickable chips that
   select/highlight those structures. Clinical notes are collapsed under "Clinical relevance"
   with a line: "Educational use only — not medical advice." Topics with no content show
   "No reviewed content yet" (keep the existing placeholders' spirit). Mark topic seen.
3. Glossary: any glossary term inside learn-panel text gets a dotted underline with a
   tooltip definition (match whole words, case-insensitive, first occurrence per block).
   Add a small "Glossary" list view in the side panel.
4. Guided tours: "Tours" button lists tours filtered/badged by level. A tour step selects
   its structures (atlas_ids and/or groups), sets the view preset, shows text with citations,
   Back/Next, step counter. If a step has "predict", first ask the learner to click where
   they think it is (or think about it), then reveal — prediction before explanation.
5. Teach before test + confidence (adaptive quiz):
   - Quiz pool for New-to-it users defaults to core topics' structures (core:true) and
     items already seen; Experts get everything. Add a "Only structures I've studied" option.
   - A new (never-seen) item is shown first as a 5-second "learn card" (highlight + name +
     beginner summary) before it is ever quizzed.
   - After each answer ask confidence: Guessed / Unsure / Knew it. Scheduling: correct+Knew
     -> box+1; correct+Guessed -> stay; wrong+Knew it (confident error) -> box 1 and show the
     topic summary immediately (hypercorrection); wrong otherwise -> box 1.
   - Add a "Function" question type from topic.checks (filtered by level) for topics whose
     structures are in the pool; show explain + citations after answering.
   - Session summary adds: calibration ("you were confident on X of Y wrong answers").
6. Leftover bugs: (a) Name it distractors must include the contralateral counterpart when it
   exists (left_X <-> right_X by atlas_id swap; e.g. left_insula vs right_insula); verify
   with insula and hippocampus. (b) Quitting a quiz must restore the camera (fitAll).
7. "About & sources" overlay: atlas attribution and 3D Slicer license link (manifest.atlas),
   "research and education only; not for clinical use", list of all content sources.

## Definition of done
Report what you changed per feature. Do not claim browser tests you did not run; Claude tests.
Only viewer/public/atlas-viewer.html changed. Stop after this task.

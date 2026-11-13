#!/usr/bin/env python3
"""Validate a NeuroApp content JSON file (neuron.json, imaging.json, ...).

Usage: python3 scripts/tests/validate_content.py viewer/public/content/neuron.json

Checks (generic, any content file):
  - top-level "sources" is an object; each source has non-empty citation, url, license
  - every source url is http(s)
  - every "cite" array anywhere in the file is a list of ids that exist in "sources"
  - no empty strings anywhere (text must not be blank)
  - every source is cited at least once (warning only)
Extra checks for neuron.json (detected by a "parts" list with "levels"):
  - fixed part ids and process ids/step keys from docs/tasks/tier6-neuron.md
  - each part: short < 90 chars, beginner 2-4 points, expert 3-5 points, every point cited
  - quiz: >= 12 items, answer index in range
Extra checks for imaging.json (detected by a "methods" list):
  - method ids in order mri, dti, ct, fmri, pet, eeg, meg; required fields present
  - short < 90 chars; every point, good_for, limits item cited; resolution ranges
    positive, low <= high, approximate true, and cited
  - eeg: 19 scalp electrodes + A1/A2 with x/y inside about the unit circle; bands cited
  - chooser: >= 8 items, answer is one of options, options are method ids
Exit code 0 when no errors, 1 otherwise.
"""
import json
import sys
from urllib.parse import urlparse

NEURON_PARTS = ["soma", "nucleus", "dendrites", "dendritic_spines", "axon_hillock", "axon",
                "myelin_sheath", "node_of_ranvier", "axon_terminals", "synapse"]
NEURON_PROCESSES = {
    "resting": ["rest"],
    "action-potential": ["rest", "threshold", "depolarization", "repolarization",
                         "hyperpolarization", "return"],
    "conduction": ["continuous", "saltatory"],
    "synapse": ["arrive", "calcium", "release", "bind", "clear"],
    "summation": ["epsp", "ipsp", "threshold"],
}


def walk(node, path, errors, cited, source_ids):
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}"
            if k == "cite":
                if not isinstance(v, list):
                    errors.append(f"{p}: cite must be a list")
                    continue
                for c in v:
                    if c not in source_ids:
                        errors.append(f"{p}: unknown source id {c!r}")
                    cited.add(c)
            elif not (path == "$" and k == "sources"):
                walk(v, p, errors, cited, source_ids)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{i}]", errors, cited, source_ids)
    elif isinstance(node, str):
        if not node.strip():
            errors.append(f"{path}: empty text")


def check_sources(data, errors):
    sources = data.get("sources")
    if not isinstance(sources, dict) or not sources:
        errors.append("$.sources: missing or empty")
        return {}
    for sid, s in sources.items():
        for field in ("citation", "url", "license"):
            if not isinstance(s.get(field), str) or not s[field].strip():
                errors.append(f"$.sources.{sid}: missing {field}")
        u = urlparse(s.get("url", ""))
        if u.scheme not in ("http", "https") or not u.netloc:
            errors.append(f"$.sources.{sid}: url is not http(s)")
    return sources


def check_neuron(data, errors):
    parts = data.get("parts", [])
    ids = [p.get("id") for p in parts]
    if sorted(ids) != sorted(NEURON_PARTS):
        errors.append(f"parts: ids {ids} != required {NEURON_PARTS}")
    for p in parts:
        pid = p.get("id")
        if len(p.get("short", "")) >= 90:
            errors.append(f"parts.{pid}.short: 90 characters or more")
        lv = p.get("levels", {})
        for level, lo, hi in (("beginner", 2, 4), ("expert", 3, 5)):
            pts = lv.get(level, {}).get("points", [])
            if not lo <= len(pts) <= hi:
                errors.append(f"parts.{pid}.{level}: {len(pts)} points (want {lo}-{hi})")
            if not lv.get(level, {}).get("summary"):
                errors.append(f"parts.{pid}.{level}: no summary")
            for i, pt in enumerate(pts):
                if not pt.get("cite"):
                    errors.append(f"parts.{pid}.{level}.points[{i}]: no cite")
        for r in p.get("related", []):
            if r not in NEURON_PARTS:
                errors.append(f"parts.{pid}.related: unknown part {r}")
    procs = {p.get("id"): p for p in data.get("processes", [])}
    for pid, keys in NEURON_PROCESSES.items():
        if pid not in procs:
            errors.append(f"processes: missing {pid}")
            continue
        got = [s.get("key") for s in procs[pid].get("steps", [])]
        if got != keys:
            errors.append(f"processes.{pid}: step keys {got} != {keys}")
        for s in procs[pid].get("steps", []):
            if not s.get("cite"):
                errors.append(f"processes.{pid}.{s.get('key')}: no cite")
            for lvl in ("beginner", "expert"):
                if not s.get("text", {}).get(lvl):
                    errors.append(f"processes.{pid}.{s.get('key')}: no {lvl} text")
    tr = procs.get("action-potential", {}).get("trace")
    if not tr or not tr.get("cite"):
        errors.append("processes.action-potential.trace: missing or uncited")
    quiz = data.get("quiz", [])
    if len(quiz) < 12:
        errors.append(f"quiz: {len(quiz)} items (want >= 12)")
    for i, q in enumerate(quiz):
        if not 0 <= q.get("answer", -1) < len(q.get("options", [])):
            errors.append(f"quiz[{i}]: answer index out of range")
        if not q.get("cite"):
            errors.append(f"quiz[{i}]: no cite")
    for i, c in enumerate(data.get("compare", {}).get("caveats", [])):
        if not c.get("cite"):
            errors.append(f"compare.caveats[{i}]: no cite")


IMAGING_METHODS = ["mri", "dti", "ct", "fmri", "pet", "eeg", "meg"]
IMAGING_ELECTRODES = {"Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "T3", "C3", "Cz", "C4", "T4",
                      "T5", "P3", "Pz", "P4", "T6", "O1", "O2", "A1", "A2"}


def check_imaging(data, errors):
    methods = data.get("methods", [])
    ids = [m.get("id") for m in methods]
    if ids != IMAGING_METHODS:
        errors.append(f"methods: ids {ids} != required order {IMAGING_METHODS}")
    for m in methods:
        mid = m.get("id")
        for field in ("name", "full", "family", "short", "measures", "levels", "good_for",
                      "limits", "experience", "resolution", "invasive", "misconception"):
            if field not in m:
                errors.append(f"methods.{mid}: missing {field}")
        if len(m.get("short", "")) >= 90:
            errors.append(f"methods.{mid}.short: 90 characters or more")
        if m.get("invasive") not in ("none", "injection", "surgery"):
            errors.append(f"methods.{mid}.invasive: bad value")
        for block in ("measures", "experience", "misconception"):
            if not m.get(block, {}).get("cite"):
                errors.append(f"methods.{mid}.{block}: no cite")
        for level in ("beginner", "expert"):
            lv = m.get("levels", {}).get(level, {})
            if not lv.get("summary"):
                errors.append(f"methods.{mid}.{level}: no summary")
            if not lv.get("points"):
                errors.append(f"methods.{mid}.{level}: no points")
            for i, pt in enumerate(lv.get("points", [])):
                if not pt.get("cite"):
                    errors.append(f"methods.{mid}.{level}.points[{i}]: no cite")
        for lst in ("good_for", "limits"):
            for i, it in enumerate(m.get(lst, [])):
                if not it.get("cite"):
                    errors.append(f"methods.{mid}.{lst}[{i}]: no cite")
        r = m.get("resolution", {})
        if not r.get("cite") or not r.get("text"):
            errors.append(f"methods.{mid}.resolution: missing text or cite")
        if r.get("approximate") is not True:
            errors.append(f"methods.{mid}.resolution: approximate must be true")
        for key in ("spatial_mm", "temporal_s"):
            v = r.get(key)
            if v is None:
                continue
            if (not isinstance(v, list) or len(v) != 2 or not all(isinstance(x, (int, float)) for x in v)
                    or v[0] <= 0 or v[0] > v[1]):
                errors.append(f"methods.{mid}.resolution.{key}: bad range {v}")
        if m.get("family") == "activity" and (r.get("spatial_mm") is None or r.get("temporal_s") is None):
            errors.append(f"methods.{mid}: activity method needs spatial and temporal ranges")
    eeg = data.get("eeg", {})
    got = {e.get("id") for e in eeg.get("electrodes", [])}
    if got != IMAGING_ELECTRODES:
        errors.append(f"eeg.electrodes: {sorted(got ^ IMAGING_ELECTRODES)} differ from the 10-20 set")
    for e in eeg.get("electrodes", []):
        x, y = e.get("x"), e.get("y")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or x * x + y * y > 1.25:
            errors.append(f"eeg.electrodes.{e.get('id')}: bad position")
        if not e.get("region"):
            errors.append(f"eeg.electrodes.{e.get('id')}: no region")
    for b in eeg.get("bands", []):
        hz = b.get("hz", [])
        if len(hz) != 2 or not 0 < hz[0] < hz[1]:
            errors.append(f"eeg.bands.{b.get('id')}: bad hz {hz}")
        if not b.get("cite"):
            errors.append(f"eeg.bands.{b.get('id')}: no cite")
    for k in ("system", "depth"):
        if not eeg.get(k, {}).get("cite"):
            errors.append(f"eeg.{k}: missing or uncited")
    ch = data.get("chooser", [])
    if len(ch) < 8:
        errors.append(f"chooser: {len(ch)} items (want >= 8)")
    for i, q in enumerate(ch):
        if q.get("answer") not in q.get("options", []):
            errors.append(f"chooser[{i}]: answer not among options")
        for o in q.get("options", []):
            if o not in IMAGING_METHODS:
                errors.append(f"chooser[{i}]: unknown option {o}")
        if not q.get("cite"):
            errors.append(f"chooser[{i}]: no cite")
    for i, g in enumerate(data.get("glossary", [])):
        if not g.get("cite"):
            errors.append(f"glossary[{i}]: no cite")


def validate(path):
    errors, warnings = [], []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    sources = check_sources(data, errors)
    cited = set()
    walk(data, "$", errors, cited, set(sources))
    for sid in sources:
        if sid not in cited:
            warnings.append(f"source {sid} is never cited")
    if isinstance(data.get("parts"), list) and data["parts"] and "levels" in data["parts"][0]:
        check_neuron(data, errors)
    if isinstance(data.get("methods"), list):
        check_imaging(data, errors)
    return errors, warnings


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    rc = 0
    for path in argv[1:]:
        errors, warnings = validate(path)
        for w in warnings:
            print(f"WARN  {path}: {w}")
        for e in errors:
            print(f"ERROR {path}: {e}")
        print(f"{path}: {'OK' if not errors else str(len(errors)) + ' error(s)'}")
        rc = rc or (1 if errors else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))

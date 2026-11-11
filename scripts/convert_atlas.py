#!/usr/bin/env python3
"""
convert_atlas.py
================
Batch-convert every mesh in brain-2017-01/models/ to GLB and write
viewer/public/atlas-manifest.json.

Identity comes from atlas metadata, not from filenames:
  atlasStructure.json  DataSource.source  ->  Structure (GeometrySelector)
  Structure LabelMapSelector.dataKey      ->  labelinfo/brain-atlas-labels-with-metadata.tsv row
  Group.member                            ->  parent groups

File selection rules
  * Every file in models/ is accounted for exactly once: exported,
    duplicate, curve, unmapped, or failed.
  * Files are deduplicated by content hash, never by the numeric model ID.
    Two files that share an ID but differ in content are both kept.
  * A file is "duplicate" only if it is byte-identical to a file that is
    exported; the manifest records which file it duplicates.
  * Hemisphere is "left"/"right" only when the atlas name says so; else null.
  * Vertex coordinates are written exactly as stored (atlas RAS space).
    The MRML applies no transform to models, so none is applied here.

Reuses read_vtk / write_glb / validate_glb from check_atlas_samples.py.

Run from anywhere:
    python3 scripts/convert_atlas.py
"""

import hashlib
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_atlas_samples import _check_vtk, read_vtk, write_glb, validate_glb  # noqa: E402

ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS_DIR   = os.path.join(ROOT, "brain-2017-01")
MODELS_DIR  = os.path.join(ATLAS_DIR, "models")
STRUCT_JSON = os.path.join(ATLAS_DIR, "atlasStructure.json")
LUT_TSV     = os.path.join(ATLAS_DIR, "labelinfo", "brain-atlas-labels-with-metadata.tsv")
OUT_DIR     = os.path.join(ROOT, "viewer", "public", "models")
MANIFEST    = os.path.join(ROOT, "viewer", "public", "atlas-manifest.json")
URL_PREFIX  = "./models/"          # relative to viewer/public/


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def as_list(x):
    return x if isinstance(x, list) else [x]


def hemisphere_of(names):
    sides = set()
    for n in names:
        found = set(re.findall(r"\b(left|right)\b", n.lower()))
        sides |= found if found else {None}
    return sides.pop() if len(sides) == 1 else None


def load_lut():
    """The label TSV uses CR line endings; parse by value."""
    with open(LUT_TSV, newline="") as fh:
        rows = re.split(r"\r\n|\r|\n", fh.read())
    header = rows[0].split("\t")
    lut = {}
    for r in rows[1:]:
        if not r.strip():
            continue
        rec = dict(zip(header, r.split("\t")))
        rec = {k: (v.strip().strip('"') or None) for k, v in rec.items()}
        lut[int(rec["value"])] = rec
    return lut


def load_metadata():
    graph = json.load(open(STRUCT_JSON))
    by_id = {n["@id"]: n for n in graph}
    ds_source = {n["@id"]: n["source"] for n in graph if n["@type"] == "DataSource"}

    parents = defaultdict(list)
    groups = []
    for n in graph:
        if n["@type"] == "Group":
            for m in n.get("member", []):
                parents[m].append(n["@id"])
            groups.append({
                "id": n["@id"].lstrip("#"),
                "name": n.get("annotation", {}).get("name"),
                "members": [m.lstrip("#") for m in n.get("member", [])],
                "color": n.get("renderOption", {}).get("color"),
            })

    file_structs = defaultdict(list)      # "Model_x.vtk" -> [Structure node]
    for n in graph:
        if n["@type"] != "Structure":
            continue
        for sel in n.get("sourceSelector", []):
            if "GeometrySelector" in as_list(sel["@type"]):
                src = ds_source[sel["dataSource"]]
                file_structs[os.path.basename(src)].append(n)

    header = next(n for n in graph if n["@type"] == "Header")
    return by_id, parents, groups, file_structs, header


def structure_record(node, parents, by_id, lut):
    label = None
    for sel in node.get("sourceSelector", []):
        if "LabelMapSelector" in as_list(sel["@type"]):
            label = sel.get("dataKey")
    lut_row = lut.get(label) if label is not None else None
    return {
        "atlas_id": node["@id"].lstrip("#"),
        "name": node.get("annotation", {}).get("name"),
        "label_value": label,
        "color": node.get("renderOption", {}).get("color"),
        "parent_groups": [
            {"id": p.lstrip("#"), "name": by_id[p].get("annotation", {}).get("name")}
            for p in parents.get(node["@id"], [])
        ],
        "radlex_id": lut_row.get("radlex_id") if lut_row else None,
        "radlex_structure_id": lut_row.get("radlex_structure_id") if lut_row else None,
        "lut_name": lut_row.get("label") if lut_row else None,
        "lut_notes": lut_row.get("notes") if lut_row else None,
    }


def geometry_kind(path):
    """Return (n_polys, n_strips, n_lines, n_verts) from the raw file."""
    import vtk
    r = vtk.vtkPolyDataReader()
    r.SetFileName(path)
    r.Update()
    p = r.GetOutput()
    return p.GetNumberOfPolys(), p.GetNumberOfStrips(), p.GetNumberOfLines(), p.GetNumberOfVerts()


def main():
    _check_vtk()
    by_id, parents, groups, file_structs, header = load_metadata()
    lut = load_lut()

    files = sorted(os.listdir(MODELS_DIR))
    hashes = {f: md5(os.path.join(MODELS_DIR, f)) for f in files}

    # Content groups: files with identical bytes.
    by_hash = defaultdict(list)
    for f in files:
        by_hash[hashes[f]].append(f)

    exported, duplicates, curves, unmapped, failures = [], [], [], [], []
    canonical_for = {}

    for h, group in by_hash.items():
        referenced = [f for f in group if f in file_structs]
        if referenced:
            # Metadata-referenced file is canonical; identical copies are duplicates.
            # Every referenced file is kept, even if bytes match another one.
            canon = referenced[0]
            for f in group:
                if f not in file_structs:
                    duplicates.append({"source": f, "duplicate_of": canon, "md5": h})
                    canonical_for[f] = canon
            for f in referenced:
                canonical_for[f] = f
        else:
            for f in group:
                if f.lower().endswith(".vtk"):
                    unmapped.append({"source": f, "md5": h, "reason": "no atlasStructure.json DataSource references this file"})
                else:
                    unmapped.append({"source": f, "md5": h, "reason": "not a .vtk mesh"})

    to_export = sorted(f for f in files if canonical_for.get(f) == f)
    os.makedirs(OUT_DIR, exist_ok=True)

    for f in to_export:
        src = os.path.join(MODELS_DIR, f)
        try:
            n_polys, n_strips, n_lines, n_verts = geometry_kind(src)
            if n_polys == 0 and n_strips == 0:
                curves.append({"source": f, "lines": n_lines, "verts": n_verts,
                               "atlas_ids": [s["@id"].lstrip("#") for s in file_structs[f]]})
                continue
            try:
                points, triangles, n_pts, n_tris = read_vtk(src)
            except SystemExit as exc:            # read_vtk exits on bad input
                raise RuntimeError(str(exc))
            if n_tris == 0:
                raise RuntimeError("0 triangles after triangulation")
            stem = os.path.splitext(f)[0]
            glb = os.path.join(OUT_DIR, stem + ".glb")
            write_glb(glb, points, triangles)
            validate_glb(glb)

            structs = [structure_record(s, parents, by_id, lut) for s in file_structs[f]]
            names = sorted({s["name"] for s in structs if s["name"]})
            px, py, pz = points[0::3], points[1::3], points[2::3]
            exported.append({
                "id": stem,
                "model_id": int(re.match(r"Model_(\d+)_", f).group(1)) if re.match(r"Model_(\d+)_", f) else None,
                "name": names[0] if len(names) == 1 else (names or [None])[0],
                "hemisphere": hemisphere_of(names) if names else None,
                "glb": URL_PREFIX + stem + ".glb",
                "source": "brain-2017-01/models/" + f,
                "source_md5": hashes[f],
                "duplicate_sources": sorted(d["source"] for d in duplicates if d["duplicate_of"] == f),
                "structures": structs,
                "vertices": n_pts,
                "triangles": n_tris,
                "line_cells_ignored": n_lines,
                "bounds_ras": [[min(px), min(py), min(pz)], [max(px), max(py), max(pz)]],
            })
            print(f"ok   {n_tris:>8,}  {f}")
        except Exception as exc:                  # record, keep going
            failures.append({"source": f, "error": f"{type(exc).__name__}: {exc}"})
            print(f"FAIL {f}: {exc}")

    license_text = open(os.path.join(ATLAS_DIR, "LICENSE.md")).read().strip()
    manifest = {
        "atlas": {
            "name": header.get("name"),
            "release": "brain-2017-01",
            "contact": header.get("contact"),
            "citation_url": "http://www.spl.harvard.edu/publications/item/view/1265",
            "license": license_text,
            "license_url": "https://github.com/Slicer/Slicer/blob/master/License.txt",
            "acknowledgement": ("Developed by the Surgical Planning Lab and Psychiatry Neuroimaging Lab, "
                                "Brigham and Women's Hospital, with NIH support under grants "
                                "P41 EB015902/RR/NIBIB (Neuroimage Analysis Center), P41 RR013218/RR/NCRR "
                                "and R01 MH050740/MH/NIMH, and a Google Research Grant."),
            "metadata_sources": ["brain-2017-01/atlasStructure.json",
                                 "brain-2017-01/labelinfo/brain-atlas-labels-with-metadata.tsv"],
        },
        "coordinates": {
            "space": "RAS (3D Slicer): +X right, +Y anterior, +Z superior",
            "transform_applied": None,
            "note": "Vertices are copied unchanged from the source .vtk files. "
                    "Apply one shared transform to all meshes in the viewer.",
        },
        "roots": [r.lstrip("#") for r in header.get("root", [])],
        "summary": {
            "source_files": len(files),
            "exported": len(exported),
            "duplicates": len(duplicates),
            "curves": len(curves),
            "unmapped": len(unmapped),
            "failures": len(failures),
        },
        "models": exported,
        "groups": groups,
        "excluded": {
            "duplicates": duplicates,
            "curves": curves,
            "unmapped": unmapped,
            "failures": failures,
        },
    }
    accounted = len(exported) + len(duplicates) + len(curves) + len(unmapped) + len(failures)
    if accounted != len(files):
        sys.exit(f"ERROR: accounted for {accounted} of {len(files)} source files")

    with open(MANIFEST, "w") as fh:
        json.dump(manifest, fh, indent=1)

    print()
    print(json.dumps(manifest["summary"], indent=1))
    print("manifest:", os.path.relpath(MANIFEST, ROOT))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
check_atlas_samples.py
======================
Read three sample VTK meshes from brain-2017-01/models/, triangulate them,
write fresh GLB files to viewer/public/models_sample/, and print one summary
line per mesh.

Run from the project root:
    python3 scripts/check_atlas_samples.py
"""

import os
import sys
import struct
import json

# ---------------------------------------------------------------------------
# Paths  (resolved relative to this file so the script works from any cwd)
# ---------------------------------------------------------------------------
ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT, "brain-2017-01", "models")
OUT_DIR    = os.path.join(ROOT, "viewer", "public", "models_sample")

SAMPLES = [
    "Model_1024_left_precentral_gyrus.vtk",
    "Model_17_left_hippocampus.vtk",
    "Model_61_medulla_oblongata.vtk",
]

# ---------------------------------------------------------------------------
# VTK reader
# ---------------------------------------------------------------------------

def _check_vtk():
    try:
        import vtk  # noqa: F401
    except ImportError:
        sys.exit("ERROR: 'vtk' Python package not found. "
                 "Install it with:  pip install vtk")


def read_vtk(path):
    """Return (points, triangles, n_pts, n_tris) after flattening strips."""
    import vtk

    if not os.path.isfile(path):
        sys.exit(f"ERROR: source file not found: {path}")

    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(path)
    reader.Update()

    poly = reader.GetOutput()
    if poly.GetNumberOfPoints() == 0:
        sys.exit(f"ERROR: vtkPolyDataReader returned 0 points for {path}")

    tri_filter = vtk.vtkTriangleFilter()
    tri_filter.SetInputData(poly)
    tri_filter.Update()
    tpoly = tri_filter.GetOutput()

    n_pts  = tpoly.GetNumberOfPoints()
    n_tris = tpoly.GetNumberOfPolys()

    pts_data = tpoly.GetPoints().GetData()
    points = [pts_data.GetValue(i)
              for i in range(pts_data.GetNumberOfTuples() * 3)]

    cells = tpoly.GetPolys()
    cells.InitTraversal()
    id_list = vtk.vtkIdList()
    triangles = []
    while cells.GetNextCell(id_list):
        if id_list.GetNumberOfIds() != 3:
            sys.exit(f"ERROR: non-triangle cell in {path} after triangulation")
        triangles.extend([id_list.GetId(0),
                          id_list.GetId(1),
                          id_list.GetId(2)])

    return points, triangles, n_pts, n_tris


# ---------------------------------------------------------------------------
# Minimal GLB writer  (binary glTF 2.0, stdlib only)
# ---------------------------------------------------------------------------

def write_glb(out_path, points, triangles):
    """Write a minimal binary glTF 2.0 file for one triangle mesh."""
    n_verts = len(points) // 3
    n_tris  = len(triangles) // 3

    idx_bytes = struct.pack(f"<{len(triangles)}I", *triangles)
    pos_bytes = struct.pack(f"<{len(points)}f",    *points)

    # Binary chunk: pad with zero bytes (spec §4.4)
    def _pad4_zero(b):
        rem = len(b) % 4
        return b + b"\x00" * (4 - rem if rem else 0)

    idx_bytes  = _pad4_zero(idx_bytes)
    pos_bytes  = _pad4_zero(pos_bytes)
    bin_data   = idx_bytes + pos_bytes
    pos_offset = len(idx_bytes)
    buf_len    = len(bin_data)

    px, py, pz = points[0::3], points[1::3], points[2::3]

    gltf = {
        "asset":  {"version": "2.0", "generator": "check_atlas_samples.py"},
        "scene":  0,
        "scenes": [{"nodes": [0]}],
        "nodes":  [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 1},
                                    "indices": 0,
                                    "mode": 4}]}],
        "accessors": [
            {
                "bufferView":    0,
                "componentType": 5125,
                "count":         n_tris * 3,
                "type":          "SCALAR",
                "min":           [0],
                "max":           [n_verts - 1],
            },
            {
                "bufferView":    1,
                "componentType": 5126,
                "count":         n_verts,
                "type":          "VEC3",
                "min":           [min(px), min(py), min(pz)],
                "max":           [max(px), max(py), max(pz)],
            },
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0,          "byteLength": len(idx_bytes),
             "target": 34963},
            {"buffer": 0, "byteOffset": pos_offset,  "byteLength": len(pos_bytes),
             "target": 34962},
        ],
        "buffers": [{"byteLength": buf_len}],
    }

    # JSON chunk: pad with spaces (spec §4.4)
    json_bytes  = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)

    total      = 12 + 8 + len(json_bytes) + 8 + buf_len
    glb_header = struct.pack("<III", 0x46546C67, 2, total)
    chunk_json = struct.pack("<II",  len(json_bytes), 0x4E4F534A) + json_bytes
    chunk_bin  = struct.pack("<II",  buf_len,          0x004E4942) + bin_data

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(glb_header + chunk_json + chunk_bin)


# ---------------------------------------------------------------------------
# Validate written GLB (header check)
# ---------------------------------------------------------------------------

def validate_glb(path):
    with open(path, "rb") as fh:
        magic, version, _total = struct.unpack("<III", fh.read(12))
    if magic != 0x46546C67:
        raise ValueError(f"bad GLB magic in {path}")
    if version != 2:
        raise ValueError(f"unexpected GLB version {version} in {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    _check_vtk()
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"{'Mesh':<45}  {'Triangles':>10}  {'GLB size':>9}  Output")
    print("-" * 100)

    for vtk_name in SAMPLES:
        vtk_path = os.path.join(MODELS_DIR, vtk_name)
        glb_path = os.path.join(OUT_DIR, os.path.splitext(vtk_name)[0] + ".glb")

        if os.path.exists(glb_path):
            os.remove(glb_path)

        points, triangles, _n_pts, n_tris = read_vtk(vtk_path)
        write_glb(glb_path, points, triangles)

        try:
            validate_glb(glb_path)
        except ValueError as exc:
            sys.exit(f"ERROR: GLB validation failed for {glb_path}: {exc}")

        glb_kb  = os.path.getsize(glb_path) / 1024
        rel_out = os.path.relpath(glb_path, ROOT)
        print(f"{vtk_name:<45}  {n_tris:>10,}  {glb_kb:>7.1f}KB  {rel_out}")

    print()
    print("All checks passed.")


if __name__ == "__main__":
    main()

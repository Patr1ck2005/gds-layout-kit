"""Generate a generic parametric layout and previews of its GDS round-trip.

Run from the repository root: python examples/public_layout.py
This sample has no process, material or device-function assumptions.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess

import gdstk
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from gds_layout_kit.primitives import make_ring_cell, make_pad_cell, make_alignment_marker_cell
from gds_layout_kit.io import write_gds, load_gds

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "showcase"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.labelsize": 8,
                         "xtick.labelsize": 8, "ytick.labelsize": 8,
                         "axes.linewidth": 0.5, "xtick.direction": "in", "ytick.direction": "in", "svg.fonttype": "none"})
    library = gdstk.Library(unit=1e-6, precision=1e-11)
    top = gdstk.Cell("PUBLIC_PARAMETRIC_SAMPLE")
    for i, outer in enumerate([4.0, 6.0, 8.0]):
        ring = make_ring_cell(f"RING_R{int(outer)}", outer, outer - 1.5)
        library.add(ring)
        for j in range(4):
            top.add(gdstk.Reference(ring, origin=(i * 24.0, j * 24.0)))
    pad = make_pad_cell("PAD", 12, 8)
    marker = make_alignment_marker_cell("MARKER", 14, 2)
    library.add(pad, marker, top)
    for y in [0.0, 24.0, 48.0, 72.0]:
        top.add(gdstk.Reference(pad, origin=(78.0, y)))
    for x in [-18.0, 102.0]:
        for y in [-18.0, 90.0]:
            top.add(gdstk.Reference(marker, origin=(x, y)))
    sample = write_gds(library, OUT / "parametric-sample.gds")
    restored = load_gds(sample)
    read_top = restored.top_level()[0]
    original_polys, polygons = top.get_polygons(), read_top.get_polygons()
    area_before, area_after = sum(p.area() for p in original_polys), sum(p.area() for p in polygons)
    assert len(polygons) == len(original_polys)
    assert np.allclose(top.bounding_box(), read_top.bounding_box(), rtol=0, atol=1e-5)
    assert np.isclose(area_before, area_after, rtol=1e-5)
    colors = {1: "#0059e8", 2: "#e60035", 3: "#00885c"}
    views = [("layout-overview", (-30, 114), (-30, 102)),
             ("layout-zoom", (36, 60), (12, 36)),
             ("layout-row", (-11, 89), (-11, 11))]
    for name, xlim, ylim in views:
        height = 80 if name == "layout-overview" else (70 if name == "layout-zoom" else 40)
        fig, ax = plt.subplots(figsize=(105 / 25.4, height / 25.4))
        for p in polygons:
            ax.add_patch(Polygon(p.points, facecolor=colors[p.layer], edgecolor="none"))
        ax.set(xlim=xlim, ylim=ylim, xlabel=r"$x$ ($\mu$m)", ylabel=r"$y$ ($\mu$m)", aspect="equal")
        fig.tight_layout(pad=0.7)
        fig.savefig(OUT / f"{name}.png", dpi=240)
        fig.savefig(OUT / f"{name}.svg")
        plt.close(fig)
    manifest = {"kind": "independently generated generic layout", "source": "examples/public_layout.py",
                "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "parameters": {"outer_radii_um": [4, 6, 8], "ring_width_um": 1.5, "pitch_um": 24,
                               "rows": 4, "pad_size_um": [12, 8], "marker_length_width_um": [14, 2],
                               "library_unit_m": restored.unit, "library_precision_m": restored.precision},
                "layers": {"1/0": "pads (blue)", "2/0": "rings (red)", "3/0": "markers (green)"},
                "checks": {"top_cell": read_top.name, "cell_count": len(restored.cells), "reference_count": len(read_top.references),
                           "flattened_polygon_count": len(polygons), "area_before_um2": area_before,
                           "area_after_um2": area_after, "bbox_um": np.asarray(read_top.bounding_box()).tolist(), "previews_source": "reloaded GDS polygons"},
                "environment": {"python": platform.python_version(), **{k: importlib.metadata.version(k) for k in ["gdstk", "matplotlib", "gds-layout-kit"]}},
                "scope": "illustrative geometry only; no fabrication rules, DRC, material model or performance result",
                "style": {"width_mm": 105, "dpi": 240, "font": "Arial", "ticks": "in", "aspect": "equal"},
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob("layout-*"))} | {sample.name: hashlib.sha256(sample.read_bytes()).hexdigest()}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["checks"], indent=2))


if __name__ == "__main__":
    main()

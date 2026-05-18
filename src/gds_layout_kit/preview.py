"""PNG preview generation for GDS cells."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

import gdstk


def save_cell_preview(
    cell: gdstk.Cell,
    path: str | Path,
    *,
    dpi: int = 200,
    facecolor: str = "white",
    edgecolor: str = "black",
) -> Path:
    """Render a simple top-cell preview to a PNG file."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    polygons = cell.get_polygons()
    bbox = cell.bounding_box()

    fig, ax = plt.subplots(figsize=(8, 6), dpi=dpi)
    ax.set_facecolor(facecolor)

    for polygon in polygons:
        patch = MplPolygon(
            polygon.points,
            closed=True,
            facecolor="#4C72B0",
            edgecolor=edgecolor,
            linewidth=0.8,
            alpha=0.75,
        )
        ax.add_patch(patch)

    if bbox is not None:
        (xmin, ymin), (xmax, ymax) = bbox
        xpad = max((xmax - xmin) * 0.08, 5.0)
        ypad = max((ymax - ymin) * 0.08, 5.0)
        ax.set_xlim(xmin - xpad, xmax + xpad)
        ax.set_ylim(ymin - ypad, ymax + ypad)

    ax.set_aspect("equal", adjustable="box")
    ax.set_title(cell.name)
    ax.set_xlabel("X (um)")
    ax.set_ylabel("Y (um)")
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.4)
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return output



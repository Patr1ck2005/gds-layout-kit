"""PNG preview generation for GDS cells.

The preview helper intentionally renders only a local center window by default.
This keeps figures readable for large layouts without touching the GDS data.
"""

from __future__ import annotations

from pathlib import Path
import math

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

import gdstk


def _bbox_width_height(bbox: tuple[tuple[float, float], tuple[float, float]]) -> tuple[float, float]:
    (xmin, ymin), (xmax, ymax) = bbox
    return xmax - xmin, ymax - ymin


def _center_crop_bbox(
    bbox: tuple[tuple[float, float], tuple[float, float]],
    crop_fraction: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    if not 0.0 < crop_fraction <= 1.0:
        raise ValueError("crop_fraction must be in (0, 1]")

    (xmin, ymin), (xmax, ymax) = bbox
    width, height = _bbox_width_height(bbox)
    crop_width = width * crop_fraction
    crop_height = height * crop_fraction
    xmid = (xmin + xmax) / 2.0
    ymid = (ymin + ymax) / 2.0
    return ((xmid - crop_width / 2.0, ymid - crop_height / 2.0), (xmid + crop_width / 2.0, ymid + crop_height / 2.0))


def _polygon_bbox(polygon: gdstk.Polygon) -> tuple[tuple[float, float], tuple[float, float]] | None:
    bbox = polygon.bounding_box()
    if bbox is not None:
        return bbox

    points = polygon.points
    if len(points) == 0:
        return None

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return ((min(xs), min(ys)), (max(xs), max(ys)))


def _bbox_intersects(
    left: tuple[tuple[float, float], tuple[float, float]],
    right: tuple[tuple[float, float], tuple[float, float]],
) -> bool:
    (lx0, ly0), (lx1, ly1) = left
    (rx0, ry0), (rx1, ry1) = right
    return not (lx1 < rx0 or rx1 < lx0 or ly1 < ry0 or ry1 < ly0)


def save_cell_preview(
    cell: gdstk.Cell,
    path: str | Path,
    *,
    crop_fraction: float = 0.2,
    pixels_per_unit: float = 12.0,
    max_total_pixels: int = 4_000_000,
    dpi: int = 100,
    facecolor: str = "white",
    edgecolor: str = "black",
) -> Path:
    """Render a cropped center-window preview to a PNG file.

    The PNG scaling is determined from the requested pixels-per-unit, then
    limited by max_total_pixels so very large layouts stay manageable.
    """

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    bbox = cell.bounding_box()
    polygons = cell.get_polygons()

    crop_bbox = None
    if bbox is not None:
        crop_bbox = _center_crop_bbox(bbox, crop_fraction)
        cropped_polygons = []
        for polygon in polygons:
            poly_bbox = _polygon_bbox(polygon)
            if poly_bbox is not None and _bbox_intersects(poly_bbox, crop_bbox):
                cropped_polygons.append(polygon)
        polygons = cropped_polygons

    view_bbox = crop_bbox or bbox
    if view_bbox is None:
        view_bbox = ((-1.0, -1.0), (1.0, 1.0))

    width_um, height_um = _bbox_width_height(view_bbox)
    width_px = max(width_um * pixels_per_unit, 64.0)
    height_px = max(height_um * pixels_per_unit, 64.0)
    estimated_pixels = width_px * height_px
    if max_total_pixels > 0 and estimated_pixels > max_total_pixels:
        scale = math.sqrt(max_total_pixels / estimated_pixels)
        width_px *= scale
        height_px *= scale

    fig, ax = plt.subplots(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
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

    (xmin, ymin), (xmax, ymax) = view_bbox
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    fig.savefig(output)
    plt.close(fig)
    return output



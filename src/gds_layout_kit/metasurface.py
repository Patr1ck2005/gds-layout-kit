"""Gradient photonic metasurface generation utilities.

This module keeps the first implementation intentionally small:
- fixed tri_factor
- x-axis gradient on the local period P
- y-axis gradient on fill
- row-wise x scaling to create a trapezoidal envelope

All coordinates are expressed in micrometers (um).
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import gdstk
from .io import write_gds
from .preview import save_cell_preview

METASURFACE_LAYER = 11


@dataclass(frozen=True)
class GradientMetasurfaceSpec:
    """Parameters for a minimal gradient metasurface demo."""

    rows: int = 160
    cols: int = 220
    pitch_min_um: float = 0.84
    pitch_max_um: float = 0.93
    fill_min: float = 0.54
    fill_max: float = 0.62
    tri_factor: float = 0.05
    trapezoid_bottom_scale: float = 1.0
    trapezoid_top_scale: float = 0.92
    outline_points: int = 240
    top_name: str = "GRADIENT_TOP"
    library_unit: float = 1e-6
    library_precision: float = 1e-9
    layer: int = METASURFACE_LAYER
    datatype: int = 0


@dataclass(frozen=True)
class GradientMetasurfaceResult:
    """Outputs of the gradient metasurface generator."""

    library: gdstk.Library
    top_cell: gdstk.Cell
    row_pitch_um: float
    x_extent_um: float
    y_extent_um: float


def _lerp(start: float, stop: float, t: float) -> float:
    return start + (stop - start) * t


def _cumulative_centers(values: list[float]) -> tuple[list[float], float]:
    centers: list[float] = []
    cursor = 0.0
    for value in values:
        centers.append(cursor + value / 2.0)
        cursor += value
    return centers, cursor


def _sample_outline(period_um: float, fill: float, tri_factor: float, outline_points: int) -> list[tuple[float, float]]:
    if period_um <= 0:
        raise ValueError("period_um must be positive")
    if not 0.0 <= fill < 1.0:
        raise ValueError("fill must be in [0, 1)")
    if outline_points < 16:
        raise ValueError("outline_points must be at least 16")
    if abs(tri_factor) >= 1.0:
        raise ValueError("tri_factor magnitude must be smaller than 1")

    r1 = period_um * math.sqrt((1.0 - fill) / math.pi)
    scale = r1 * (1.0 - tri_factor * tri_factor) ** 0.75

    points: list[tuple[float, float]] = []
    for index in range(outline_points):
        s = 2.0 * math.pi * index / outline_points
        denom = 1.0 - tri_factor * math.cos(3.0 * s)
        x = -math.sin(s) * scale / denom
        y = math.cos(s) * scale / denom
        points.append((x, y))
    return points


def _translate_points(points: list[tuple[float, float]], dx: float, dy: float) -> list[tuple[float, float]]:
    return [(x + dx, y + dy) for x, y in points]


def build_gradient_metasurface_layout(spec: GradientMetasurfaceSpec) -> GradientMetasurfaceResult:
    """Build a gradient metasurface layout with row-wise trapezoidal scaling.

    The implementation is intentionally direct: each row is built as a dedicated
    cell with a y-gradient in fill, while the local x-scale is varied per row to
    create a trapezoidal envelope. Inside each row, the local period P varies
    along x.
    """

    if spec.rows < 2 or spec.cols < 2:
        raise ValueError("rows and cols must both be at least 2")
    if spec.pitch_min_um <= 0 or spec.pitch_max_um <= 0:
        raise ValueError("pitch values must be positive")
    if spec.pitch_min_um > spec.pitch_max_um:
        raise ValueError("pitch_min_um must be <= pitch_max_um")
    if not 0.0 <= spec.fill_min < spec.fill_max < 1.0:
        raise ValueError("fill range must satisfy 0 <= fill_min < fill_max < 1")
    if spec.trapezoid_bottom_scale <= 0 or spec.trapezoid_top_scale <= 0:
        raise ValueError("trapezoid scales must be positive")

    library = gdstk.Library(unit=spec.library_unit, precision=spec.library_precision)
    top_cell = gdstk.Cell(spec.top_name)

    pitch_values = [
        _lerp(spec.pitch_min_um, spec.pitch_max_um, index / (spec.cols - 1))
        for index in range(spec.cols)
    ]
    x_centers, x_extent_um = _cumulative_centers(pitch_values)
    x_center_offset = x_extent_um / 2.0
    nominal_row_pitch_um = sum(pitch_values) / len(pitch_values)
    y_extent_um = nominal_row_pitch_um * spec.rows

    for row_index in range(spec.rows):
        y_t = row_index / (spec.rows - 1)
        fill = _lerp(spec.fill_min, spec.fill_max, y_t)
        row_scale = _lerp(spec.trapezoid_bottom_scale, spec.trapezoid_top_scale, y_t)
        row_cell = gdstk.Cell(f"ROW_{row_index:04d}")

        for col_index, period_um in enumerate(pitch_values):
            outline = _sample_outline(period_um, fill, spec.tri_factor, spec.outline_points)
            x_center = (x_centers[col_index] - x_center_offset) * row_scale
            scaled_outline = [(x * row_scale, y) for x, y in outline]
            row_cell.add(
                gdstk.Polygon(
                    _translate_points(scaled_outline, x_center, 0.0),
                    layer=spec.layer,
                    datatype=spec.datatype,
                )
            )

        y_center = (row_index - (spec.rows - 1) / 2.0) * nominal_row_pitch_um
        top_cell.add(gdstk.Reference(row_cell, origin=(0.0, y_center)))
        library.add(row_cell)

    library.add(top_cell)
    return GradientMetasurfaceResult(
        library=library,
        top_cell=top_cell,
        row_pitch_um=nominal_row_pitch_um,
        x_extent_um=x_extent_um,
        y_extent_um=y_extent_um,
    )


def save_gradient_layout_files(result: GradientMetasurfaceResult, gds_path: str | Path, png_path: str | Path) -> tuple[Path, Path]:
    """Write GDS and PNG preview for a generated gradient metasurface result.

    Returns the resolved paths (gds_path, png_path).
    """

    # Write GDS library
    gds_out = write_gds(result.library, gds_path)

    # Render a preview of the top cell
    png_out = save_cell_preview(result.top_cell, png_path)

    return gds_out, png_out



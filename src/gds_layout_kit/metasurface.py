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
class GradientMetasurfaceSpecBase:
    """Common parameters for gradient metasurface layouts."""

    rows: int = 160
    cols: int = 220
    outline_points: int = 240
    top_name: str = "GRADIENT_TOP"
    library_unit: float = 1e-6
    library_precision: float = 1e-9
    layer: int = METASURFACE_LAYER
    datatype: int = 0


@dataclass(frozen=True)
class TrapezoidalGradientMetasurfaceSpec(GradientMetasurfaceSpecBase):
    """Specialized spec for trapezoidal gradient metasurface with period and fill gradients.

    The layout is generated as follows:
    - Y-axis: fill gradient from fill_min to fill_max
    - X-axis: period gradient from pitch_min_um to pitch_max_um, achieved via coordinate scaling
    - Fill is preserved during scaling; the trapezoid boundary emerges naturally

    Parameters:
    - center_aligned: if True, creates an isosceles trapezoid (center row x-aligned);
                      if False, creates a right trapezoid (bottom row x-aligned)
    """

    pitch_min_um: float = 0.84
    pitch_max_um: float = 0.93
    fill_min: float = 0.54
    fill_max: float = 0.62
    tri_factor: float = 0.05
    center_aligned: bool = True


class GradientMetasurfaceSpec(TrapezoidalGradientMetasurfaceSpec):
    """Backward-compatible alias for the trapezoidal gradient spec."""


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


def build_trapezoidal_gradient_metasurface_layout(
    spec: TrapezoidalGradientMetasurfaceSpec,
) -> GradientMetasurfaceResult:
    """Build a gradient metasurface layout using grid coordinate transformation.

    The layout is constructed as follows:
    1. Generate a standard rectangular grid with all cells at pitch_avg
    2. Generate patterns in this standard grid (fill gradient on y-axis, constant pitch on x-axis)
    3. Apply a non-uniform coordinate transformation to create the trapezoid:
       - x-direction: scale each column by its local period ratio (preserves adjacency)
       - y-direction: remain uniform (no y-axis period gradient)
    4. Fill is preserved because it's only a coordinate transformation, not a geometric deformation
    """

    if spec.rows < 2 or spec.cols < 2:
        raise ValueError("rows and cols must both be at least 2")
    if spec.pitch_min_um <= 0 or spec.pitch_max_um <= 0:
        raise ValueError("pitch values must be positive")
    if spec.pitch_min_um > spec.pitch_max_um:
        raise ValueError("pitch_min_um must be <= pitch_max_um")
    if not 0.0 <= spec.fill_min < spec.fill_max < 1.0:
        raise ValueError("fill range must satisfy 0 <= fill_min < fill_max < 1")

    library = gdstk.Library(unit=spec.library_unit, precision=spec.library_precision)
    top_cell = gdstk.Cell(spec.top_name)

    # Compute the average pitch and target period values for each column
    pitch_values = [
        _lerp(spec.pitch_min_um, spec.pitch_max_um, index / (spec.cols - 1))
        for index in range(spec.cols)
    ]
    avg_pitch_um = sum(pitch_values) / len(pitch_values)

    # Pre-compute column x-offsets for the transformed grid
    col_x_offsets = []
    cumulative_x = 0.0
    for col_index in range(spec.cols):
        col_x_offsets.append(cumulative_x)
        cumulative_x += pitch_values[col_index]

    x_extent_um = cumulative_x
    # Pre-compute y-offsets for center alignment (isosceles trapezoid)
    col_y_offsets = [0.0] * spec.cols
    if spec.center_aligned:
        center_row_idx = (spec.rows - 1) / 2.0
        # Target y-position at the center row (using the minimum pitch column as reference)
        y_mid_target = center_row_idx * pitch_values[0] + pitch_values[0] / 2.0
        # For each column, compute the y-offset needed so center row aligns to y_mid_target
        for col_idx in range(spec.cols):
            col_y_at_mid = center_row_idx * pitch_values[col_idx] + pitch_values[col_idx] / 2.0
            col_y_offsets[col_idx] = y_mid_target - col_y_at_mid
    
    # Calculate y_extent: max y - min y across all positions
    min_y = float('inf')
    max_y = float('-inf')
    for row_idx in range(spec.rows):
        for col_idx in range(spec.cols):
            y_pos = row_idx * pitch_values[col_idx] + pitch_values[col_idx] / 2.0 + col_y_offsets[col_idx]
            min_y = min(min_y, y_pos)
            max_y = max(max_y, y_pos)
    y_extent_um = max_y - min_y

    # Create a single layout cell with all patterns directly in trapezoid grid
    layout_cell = gdstk.Cell("LAYOUT")
    
    for row_index in range(spec.rows):
        y_t = row_index / (spec.rows - 1)
        fill = _lerp(spec.fill_min, spec.fill_max, y_t)

        # For each position in the trapezoid grid
        for col_index in range(spec.cols):
            col_pitch = pitch_values[col_index]

            # Generate pattern using this column's actual period
            outline = _sample_outline(col_pitch, fill, spec.tri_factor, spec.outline_points)
            
            # Position in trapezoid grid:
            # x-position: cumulative offset + half this column's period
            col_x_center = col_x_offsets[col_index] + col_pitch / 2.0
            
            # y-position: each column has its own row height based on its period
            # plus a per-column y-offset to achieve center alignment if requested
            row_y_center = row_index * col_pitch + col_pitch / 2.0 + col_y_offsets[col_index]

            # Translate the outline to this position
            translated_outline = _translate_points(outline, col_x_center, row_y_center)
            
            layout_cell.add(
                gdstk.Polygon(
                    translated_outline,
                    layer=spec.layer,
                    datatype=spec.datatype,
                )
            )

    library.add(layout_cell)
    top_cell.add(gdstk.Reference(layout_cell, origin=(0.0, 0.0)))
    library.add(top_cell)

    return GradientMetasurfaceResult(
        library=library,
        top_cell=top_cell,
        row_pitch_um=avg_pitch_um,
        x_extent_um=x_extent_um,
        y_extent_um=y_extent_um,
    )


def build_gradient_metasurface_layout(spec: TrapezoidalGradientMetasurfaceSpec) -> GradientMetasurfaceResult:
    """Compatibility wrapper for the trapezoidal gradient layout builder."""

    return build_trapezoidal_gradient_metasurface_layout(spec)


def save_trapezoidal_gradient_layout_files(
    result: GradientMetasurfaceResult,
    gds_path: str | Path,
    png_path: str | Path,
    *,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 12.0,
    preview_max_total_pixels: int = 4_000_000,
) -> tuple[Path, Path]:
    """Write GDS and PNG preview for a generated gradient metasurface result.

    Returns the resolved paths (gds_path, png_path).
    """

    # Write GDS library
    gds_out = write_gds(result.library, gds_path)

    # Render a preview of the top cell
    png_out = save_cell_preview(
        result.top_cell,
        png_path,
        crop_fraction=preview_crop_fraction,
        pixels_per_unit=preview_pixels_per_unit,
        max_total_pixels=preview_max_total_pixels,
    )

    return gds_out, png_out


def save_gradient_layout_files(
    result: GradientMetasurfaceResult,
    gds_path: str | Path,
    png_path: str | Path,
    *,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 12.0,
    preview_max_total_pixels: int = 4_000_000,
) -> tuple[Path, Path]:
    """Compatibility wrapper for the trapezoidal gradient layout writer."""

    return save_trapezoidal_gradient_layout_files(
        result,
        gds_path,
        png_path,
        preview_crop_fraction=preview_crop_fraction,
        preview_pixels_per_unit=preview_pixels_per_unit,
        preview_max_total_pixels=preview_max_total_pixels,
    )



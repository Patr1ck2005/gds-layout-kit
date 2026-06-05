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
from .transform import (
    TrapezoidalGradientTransform,
    apply_transform_to_polygons,
    compute_trapezoid_extents,
)

METASURFACE_LAYER = 11


GRID_LAYER = 12


@dataclass(frozen=True)
class GradientMetasurfaceSpecBase:
    """Common parameters for gradient metasurface layouts."""

    rows: int = 160
    cols: int = 220
    outline_points: int = 240
    top_name: str = "GRADIENT_TOP"
    library_unit: float = 1e-6
    library_precision: float = 1e-11
    layer: int = METASURFACE_LAYER
    datatype: int = 0
    show_grid: bool = True
    grid_layer: int = GRID_LAYER
    grid_datatype: int = 0
    grid_line_width_um: float = 0.01


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
    show_grid: bool = False
    grid_layer: int = GRID_LAYER
    grid_datatype: int = 0


def _lerp(start: float, stop: float, t: float) -> float:
    return start + (stop - start) * t



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


def _build_uniform_polygons(
    spec: TrapezoidalGradientMetasurfaceSpec,
    base_period_um: float,
) -> list[list[tuple[float, float]]]:
    """Generate all patterns in a uniform rectangular grid with spacing base_period_um.

    Fill varies row-by-row; every column in the same row uses the identical
    pattern outline, only translated.
    """
    polygons: list[list[tuple[float, float]]] = []
    for row_index in range(spec.rows):
        y_t = row_index / (spec.rows - 1)
        fill = _lerp(spec.fill_min, spec.fill_max, y_t)
        outline = _sample_outline(base_period_um, fill, spec.tri_factor, spec.outline_points)
        for col_index in range(spec.cols):
            cx = (col_index + 0.5) * base_period_um
            cy = (row_index + 0.5) * base_period_um
            polygons.append(_translate_points(outline, cx, cy))
    return polygons


def _build_grid_polygons(
    spec: TrapezoidalGradientMetasurfaceSpec,
    base_period_um: float,
    transform: TrapezoidalGradientTransform,
) -> list[list[tuple[float, float]]]:
    """Generate thin rectangular polygons tracing the transformed grid lines."""
    half_w = spec.grid_line_width_um / 2.0
    rows = spec.rows
    cols = spec.cols

    # Transform all grid corner points
    grid_pts: dict[tuple[int, int], tuple[float, float]] = {}
    for i in range(rows + 1):
        for j in range(cols + 1):
            ux = j * base_period_um
            uy = i * base_period_um
            grid_pts[(i, j)] = transform.transform_point(ux, uy)

    polygons: list[list[tuple[float, float]]] = []

    def _add_segment(p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-15:
            return
        nx = -dy / length * half_w
        ny = dx / length * half_w
        polygons.append([
            (p1[0] + nx, p1[1] + ny),
            (p1[0] - nx, p1[1] - ny),
            (p2[0] - nx, p2[1] - ny),
            (p2[0] + nx, p2[1] + ny),
        ])

    # Horizontal segments
    for i in range(rows + 1):
        for j in range(cols):
            _add_segment(grid_pts[(i, j)], grid_pts[(i, j + 1)])

    # Vertical segments
    for j in range(cols + 1):
        for i in range(rows):
            _add_segment(grid_pts[(i, j)], grid_pts[(i + 1, j)])

    return polygons


def build_trapezoidal_gradient_metasurface_layout(
    spec: TrapezoidalGradientMetasurfaceSpec,
) -> GradientMetasurfaceResult:
    """Build a gradient metasurface via uniform-grid generation + global coordinate transform.

    The layout is constructed in two stages:
    1. All patterns are generated with the same base period in a uniform
       rectangular grid (fill varies row-by-row).
    2. A smooth continuous coordinate transformation warps the entire layout,
       creating the period gradient and trapezoid envelope.  Patterns are
       subtly distorted because the warp is nonlinear.
    """

    if spec.rows < 2 or spec.cols < 2:
        raise ValueError("rows and cols must both be at least 2")
    if spec.pitch_min_um <= 0 or spec.pitch_max_um <= 0:
        raise ValueError("pitch values must be positive")
    if spec.pitch_min_um > spec.pitch_max_um:
        raise ValueError("pitch_min_um must be <= pitch_max_um")
    if not 0.0 <= spec.fill_min < spec.fill_max < 1.0:
        raise ValueError("fill range must satisfy 0 <= fill_min < fill_max < 1")

    base_period_um = spec.pitch_min_um

    # Stage 1: uniform rectangular grid
    uniform_polygons = _build_uniform_polygons(spec, base_period_um)

    # Stage 2: global coordinate transformation
    transform = TrapezoidalGradientTransform(
        pitch_min_um=spec.pitch_min_um,
        pitch_max_um=spec.pitch_max_um,
        base_period_um=base_period_um,
        num_cols=spec.cols,
        num_rows=spec.rows,
        center_aligned=spec.center_aligned,
    )
    transformed_polygons = apply_transform_to_polygons(uniform_polygons, transform)

    # Build gdstk output
    library = gdstk.Library(unit=spec.library_unit, precision=spec.library_precision)
    top_cell = gdstk.Cell(spec.top_name)
    layout_cell = gdstk.Cell("LAYOUT")

    for outline in transformed_polygons:
        layout_cell.add(
            gdstk.Polygon(outline, layer=spec.layer, datatype=spec.datatype),
        )

    # Optional grid overlay
    if spec.show_grid:
        grid_polygons = _build_grid_polygons(spec, base_period_um, transform)
        for outline in grid_polygons:
            layout_cell.add(
                gdstk.Polygon(outline, layer=spec.grid_layer, datatype=spec.grid_datatype),
            )

    library.add(layout_cell)
    top_cell.add(gdstk.Reference(layout_cell, origin=(0.0, 0.0)))
    library.add(top_cell)

    x_extent_um, y_extent_um = compute_trapezoid_extents(
        pitch_min_um=spec.pitch_min_um,
        pitch_max_um=spec.pitch_max_um,
        num_cols=spec.cols,
        num_rows=spec.rows,
        center_aligned=spec.center_aligned,
    )
    avg_pitch_um = (spec.pitch_min_um + spec.pitch_max_um) / 2.0

    return GradientMetasurfaceResult(
        library=library,
        top_cell=top_cell,
        row_pitch_um=avg_pitch_um,
        x_extent_um=x_extent_um,
        y_extent_um=y_extent_um,
        show_grid=spec.show_grid,
        grid_layer=spec.grid_layer,
        grid_datatype=spec.grid_datatype,
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
) -> tuple[Path, Path, Path | None]:
    """Write GDS and PNG preview for a generated gradient metasurface result.

    When *result.show_grid* is True, also writes a separate grid-only GDS.
    Returns (gds_path, png_path, grid_gds_path_or_None).
    """

    gds_out = write_gds(result.library, gds_path)

    # Optional grid-only GDS
    grid_out: Path | None = None
    if result.show_grid:
        grid_lib = gdstk.Library(
            unit=result.library.unit, precision=result.library.precision
        )
        grid_cell = gdstk.Cell("GRID")
        # Extract grid-layer polygons from the layout cell
        for cell in result.library.cells:
            if cell.name == "LAYOUT":
                for poly in cell.polygons:
                    if poly.layer == result.grid_layer and poly.datatype == result.grid_datatype:
                        grid_cell.add(gdstk.Polygon(poly.points, layer=result.grid_layer, datatype=result.grid_datatype))
                break
        grid_top = gdstk.Cell(result.top_cell.name + "_GRID")
        grid_top.add(gdstk.Reference(grid_cell))
        grid_lib.add(grid_cell, grid_top)

        gds_path_obj = Path(gds_path)
        grid_path = gds_path_obj.parent / f"{gds_path_obj.stem}_grid{gds_path_obj.suffix}"
        grid_out = write_gds(grid_lib, grid_path)

    png_out = save_cell_preview(
        result.top_cell,
        png_path,
        crop_fraction=preview_crop_fraction,
        pixels_per_unit=preview_pixels_per_unit,
        max_total_pixels=preview_max_total_pixels,
    )

    return gds_out, png_out, grid_out


def save_gradient_layout_files(
    result: GradientMetasurfaceResult,
    gds_path: str | Path,
    png_path: str | Path,
    *,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 12.0,
    preview_max_total_pixels: int = 4_000_000,
) -> tuple[Path, Path, Path | None]:
    """Compatibility wrapper for the trapezoidal gradient layout writer."""

    return save_trapezoidal_gradient_layout_files(
        result,
        gds_path,
        png_path,
        preview_crop_fraction=preview_crop_fraction,
        preview_pixels_per_unit=preview_pixels_per_unit,
        preview_max_total_pixels=preview_max_total_pixels,
    )



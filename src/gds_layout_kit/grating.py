"""Grating gradient layout generation.

Grating lines (vertical strips) with period gradient along X and
duty cycle gradient along Y, making each line trapezoidal.

By default the array is rectangular (no trapezoidal envelope) because
grating lines are continuous vertical strips -- the functional information
is in the period and DC gradients, not the boundary shape.

Set ``rectangular=False`` to apply the trapezoidal envelope transform.

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

GRATING_LAYER = 11
GRATING_GRID_LAYER = 12


@dataclass(frozen=True)
class GratingGradientSpec:
    """Specification for a grating gradient layout.

    Parameters
    ----------
    rows, cols: Grid dimensions (must be >= 2).
    pitch_min_um: Minimum local period in um, leftmost column. Default 0.5 (500 nm).
    pitch_max_um: Maximum local period in um, rightmost column. Default 0.6 (600 nm).
    dc_min: Minimum duty cycle at bottom row. Default 0.4.
    dc_max: Maximum duty cycle at top row. Default 0.6.
    rectangular: If True (default), generate a plain rectangular array with
        directly varying column periods and row DC.  If False, apply the
        trapezoidal envelope transform (isosceles or right trapezoid).
    center_aligned: When rectangular=False, controls isosceles vs right trapezoid.
    tone: ``"positive"`` draws grating lines as solids;
          ``"negative"`` subtracts them from a background rectangle.
    """

    rows: int = 160
    cols: int = 220
    pitch_min_um: float = 0.5
    pitch_max_um: float = 0.6
    dc_min: float = 0.4
    dc_max: float = 0.6
    rectangular: bool = True
    center_aligned: bool = True
    tone: str = "positive"
    top_name: str = "GRATING_GRADIENT_TOP"
    library_unit: float = 1e-6
    library_precision: float = 1e-9
    layer: int = GRATING_LAYER
    datatype: int = 0
    show_grid: bool = False
    grid_layer: int = GRATING_GRID_LAYER
    grid_datatype: int = 0
    grid_line_width_um: float = 0.01


@dataclass(frozen=True)
class GratingGradientResult:
    """Outputs of the grating gradient generator."""

    library: gdstk.Library
    top_cell: gdstk.Cell
    x_extent_um: float
    y_extent_um: float
    show_grid: bool = False
    grid_layer: int = GRATING_GRID_LAYER
    grid_datatype: int = 0


def _lerp(start: float, stop: float, t: float) -> float:
    return start + (stop - start) * t


def _build_rectangular_grating_polygons(
    spec: GratingGradientSpec,
) -> tuple[list[list[tuple[float, float]]], list[float], list[float], float]:
    """Generate one trapezoid polygon per grating line (column).

    Each column j produces a single polygon whose width varies linearly
    from dc_min at the bottom to dc_max at the top, forming a true
    trapezoid.  Period varies column-by-column.

    Returns (polygons, col_x_starts, col_periods, row_height).
    """
    row_height = (spec.pitch_min_um + spec.pitch_max_um) / 2.0
    total_height = spec.rows * row_height

    col_periods: list[float] = []
    col_x_starts: list[float] = []
    x_cursor = 0.0
    denom = spec.cols - 1 if spec.cols > 1 else 1.0
    for j in range(spec.cols):
        t = j / denom
        period = _lerp(spec.pitch_min_um, spec.pitch_max_um, t)
        col_periods.append(period)
        col_x_starts.append(x_cursor)
        x_cursor += period

    polygons: list[list[tuple[float, float]]] = []
    for j in range(spec.cols):
        period_j = col_periods[j]
        cx = col_x_starts[j] + period_j / 2.0

        half_w_bottom = spec.dc_min * period_j / 2.0
        half_w_top = spec.dc_max * period_j / 2.0

        if half_w_bottom <= 0.0 and half_w_top <= 0.0:
            continue

        polygons.append([
            (cx - half_w_bottom, 0.0),
            (cx + half_w_bottom, 0.0),
            (cx + half_w_top, total_height),
            (cx - half_w_top, total_height),
        ])

    return polygons, col_x_starts, col_periods, row_height


def _build_rectangular_grid_polygons(
    spec: GratingGradientSpec,
    col_x_starts: list[float],
    col_periods: list[float],
    row_height: float,
) -> list[list[tuple[float, float]]]:
    """Grid lines for a rectangular grating layout."""
    half_w = spec.grid_line_width_um / 2.0
    rows = spec.rows
    cols = spec.cols

    col_edges = col_x_starts + [col_x_starts[-1] + col_periods[-1]]
    row_edges = [i * row_height for i in range(rows + 1)]

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

    for i in range(rows + 1):
        y = row_edges[i]
        for j in range(cols):
            _add_segment((col_edges[j], y), (col_edges[j + 1], y))

    for j in range(cols + 1):
        x = col_edges[j]
        for i in range(rows):
            _add_segment((x, row_edges[i]), (x, row_edges[i + 1]))

    return polygons


def _build_uniform_grating_polygons(
    spec: GratingGradientSpec,
    base_period_um: float,
) -> list[list[tuple[float, float]]]:
    """Generate rectangular grating lines in a uniform square grid.

    Each unit cell contains a centered rectangle:
      - width  = dc(row) * base_period_um
      - height = base_period_um  (fills cell height -> continuous lines)

    DC varies row-by-row; every column in the same row uses the identical
    rectangle geometry, only translated.
    """
    polygons: list[list[tuple[float, float]]] = []
    half_h = base_period_um / 2.0

    for row_index in range(spec.rows):
        y_t = row_index / (spec.rows - 1)
        dc = _lerp(spec.dc_min, spec.dc_max, y_t)
        half_w = dc * base_period_um / 2.0

        if half_w <= 0.0:
            continue

        for col_index in range(spec.cols):
            cx = (col_index + 0.5) * base_period_um
            cy = (row_index + 0.5) * base_period_um
            polygons.append([
                (cx - half_w, cy - half_h),
                (cx + half_w, cy - half_h),
                (cx + half_w, cy + half_h),
                (cx - half_w, cy + half_h),
            ])

    return polygons


def _build_grid_polygons(
    spec: GratingGradientSpec,
    base_period_um: float,
    transform: TrapezoidalGradientTransform,
) -> list[list[tuple[float, float]]]:
    """Generate thin rectangular polygons tracing the transformed grid lines."""
    half_w = spec.grid_line_width_um / 2.0
    rows = spec.rows
    cols = spec.cols

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

    for i in range(rows + 1):
        for j in range(cols):
            _add_segment(grid_pts[(i, j)], grid_pts[(i, j + 1)])

    for j in range(cols + 1):
        for i in range(rows):
            _add_segment(grid_pts[(i, j)], grid_pts[(i + 1, j)])

    return polygons


def _tone_invert(
    grating_polygons: list[gdstk.Polygon],
    x_extent_um: float,
    y_extent_um: float,
    y_min: float,
    spec: GratingGradientSpec,
) -> list[gdstk.Polygon]:
    """Subtract grating polygons from a background rectangle."""
    margin = 0.01 * max(x_extent_um, y_extent_um)
    bg_y_min = y_min - margin
    bg_x_max = x_extent_um + margin
    bg_y_max = bg_y_min + y_extent_um + 2.0 * margin

    background = gdstk.rectangle(
        (0.0, bg_y_min), (bg_x_max, bg_y_max),
        layer=spec.layer, datatype=spec.datatype,
    )
    return list(gdstk.boolean(
        [background], grating_polygons, "not",
        precision=spec.library_precision,
        layer=spec.layer, datatype=spec.datatype,
    ))


def build_grating_gradient_layout(
    spec: GratingGradientSpec,
) -> GratingGradientResult:
    """Build a grating gradient layout.

    Two modes (controlled by *spec.rectangular*):

    **Rectangular mode** (default):
        Columns are placed at directly varying periods (pitch_min .. pitch_max)
        and rows have constant height.  The array is a plain rectangle.

    **Trapezoidal mode** (``rectangular=False``):
        Two-stage pipeline -- uniform grid then TrapezoidalGradientTransform.
    """

    if spec.rows < 2 or spec.cols < 2:
        raise ValueError("rows and cols must both be at least 2")
    if spec.pitch_min_um <= 0 or spec.pitch_max_um <= 0:
        raise ValueError("pitch values must be positive")
    if spec.pitch_max_um < spec.pitch_min_um:
        raise ValueError("pitch_max_um must be >= pitch_min_um")
    if not (0.0 <= spec.dc_min < spec.dc_max < 1.0):
        raise ValueError("dc range must satisfy 0 <= dc_min < dc_max < 1")
    if spec.tone not in ("positive", "negative"):
        raise ValueError(f"tone must be 'positive' or 'negative', got {spec.tone!r}")

    library = gdstk.Library(unit=spec.library_unit, precision=spec.library_precision)
    layout_cell = gdstk.Cell("LAYOUT")

    if spec.rectangular:
        # --- Rectangular: direct placement with varying column periods ---
        outlines, col_x_starts, col_periods, row_height = _build_rectangular_grating_polygons(spec)

        x_extent_um = col_x_starts[-1] + col_periods[-1]
        y_extent_um = spec.rows * row_height
        y_min = 0.0

        grating_polygons = [
            gdstk.Polygon(pts, layer=spec.layer, datatype=spec.datatype)
            for pts in outlines
        ]

        if spec.tone == "negative":
            final_polygons = _tone_invert(grating_polygons, x_extent_um, y_extent_um, y_min, spec)
            for poly in final_polygons:
                layout_cell.add(poly)
        else:
            for poly in grating_polygons:
                layout_cell.add(poly)

        if spec.show_grid:
            grid_polygons = _build_rectangular_grid_polygons(spec, col_x_starts, col_periods, row_height)
            for outline in grid_polygons:
                layout_cell.add(
                    gdstk.Polygon(outline, layer=spec.grid_layer, datatype=spec.grid_datatype),
                )

    else:
        # --- Trapezoidal: uniform grid + coordinate transform ---
        base_period_um = spec.pitch_min_um
        uniform_polygons = _build_uniform_grating_polygons(spec, base_period_um)

        transform = TrapezoidalGradientTransform(
            pitch_min_um=spec.pitch_min_um,
            pitch_max_um=spec.pitch_max_um,
            base_period_um=base_period_um,
            num_cols=spec.cols,
            num_rows=spec.rows,
            center_aligned=spec.center_aligned,
        )
        transformed_polygons = apply_transform_to_polygons(uniform_polygons, transform)

        x_extent_um, y_extent_um = compute_trapezoid_extents(
            pitch_min_um=spec.pitch_min_um,
            pitch_max_um=spec.pitch_max_um,
            num_cols=spec.cols,
            num_rows=spec.rows,
            center_aligned=spec.center_aligned,
        )
        y_min = -y_extent_um / 2.0 if spec.center_aligned else 0.0

        grating_polygons = [
            gdstk.Polygon(pts, layer=spec.layer, datatype=spec.datatype)
            for pts in transformed_polygons
        ]

        if spec.tone == "negative":
            final_polygons = _tone_invert(grating_polygons, x_extent_um, y_extent_um, y_min, spec)
            for poly in final_polygons:
                layout_cell.add(poly)
        else:
            for poly in grating_polygons:
                layout_cell.add(poly)

        if spec.show_grid:
            grid_polygons = _build_grid_polygons(spec, base_period_um, transform)
            for outline in grid_polygons:
                layout_cell.add(
                    gdstk.Polygon(outline, layer=spec.grid_layer, datatype=spec.grid_datatype),
                )

    top_cell = gdstk.Cell(spec.top_name)
    library.add(layout_cell)
    top_cell.add(gdstk.Reference(layout_cell, origin=(0.0, 0.0)))
    library.add(top_cell)

    return GratingGradientResult(
        library=library,
        top_cell=top_cell,
        x_extent_um=x_extent_um,
        y_extent_um=y_extent_um,
        show_grid=spec.show_grid,
        grid_layer=spec.grid_layer,
        grid_datatype=spec.grid_datatype,
    )


def save_grating_gradient_layout_files(
    result: GratingGradientResult,
    gds_path: str | Path,
    png_path: str | Path,
    *,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 12.0,
    preview_max_total_pixels: int = 4_000_000,
    preview_edgecolor: str = "none",
) -> tuple[Path, Path, Path | None]:
    """Write GDS and PNG preview for a generated grating gradient result.

    When *result.show_grid* is True, also writes a separate grid-only GDS.
    Returns (gds_path, png_path, grid_gds_path_or_None).
    """

    gds_out = write_gds(result.library, gds_path)

    grid_out: Path | None = None
    if result.show_grid:
        grid_lib = gdstk.Library(
            unit=result.library.unit, precision=result.library.precision
        )
        grid_cell = gdstk.Cell("GRID")
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
        edgecolor=preview_edgecolor,
    )

    return gds_out, png_out, grid_out

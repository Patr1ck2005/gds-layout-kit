"""Executable demo for the gradient metasurface example."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .io import load_gds, top_cell_summary
from .metasurface import (
    TrapezoidalGradientMetasurfaceSpec,
    build_trapezoidal_gradient_metasurface_layout,
    save_trapezoidal_gradient_layout_files,
)


@dataclass(frozen=True)
class GradientDemoResult:
    spec: TrapezoidalGradientMetasurfaceSpec
    x_extent_um: float
    y_extent_um: float
    gds_path: Path
    png_path: Path
    summary: list[dict[str, object]]


def _derive_grid_dimension(layout_um: float, pitch_min_um: float, pitch_max_um: float) -> int:
    if layout_um <= 0:
        raise ValueError("layout size must be positive")
    if pitch_min_um <= 0 or pitch_max_um <= 0:
        raise ValueError("pitch values must be positive")

    mean_pitch = (pitch_min_um + pitch_max_um) / 2.0
    return max(2, int(round(layout_um / mean_pitch)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a gradient photonic metasurface GDS and PNG preview.")
    parser.add_argument("--layout-width-um", type=float, default=10.0, help="Target layout width in um when rows/cols are not given.")
    parser.add_argument("--layout-height-um", type=float, default=10.0, help="Target layout height in um when rows/cols are not given.")
    parser.add_argument("--rows", type=int, default=None, help="Number of rows; defaults are derived from layout height.")
    parser.add_argument("--cols", type=int, default=None, help="Number of columns; defaults are derived from layout width.")
    parser.add_argument("--pitch-min-um", type=float, default=0.84/2, help="Minimum local period P in um.")
    parser.add_argument("--pitch-max-um", type=float, default=0.93, help="Maximum local period P in um.")
    parser.add_argument("--fill-min", type=float, default=0.54, help="Minimum fill factor.")
    parser.add_argument("--fill-max", type=float, default=0.62, help="Maximum fill factor.")
    parser.add_argument("--tri-factor", type=float, default=0.05, help="Triangular deformation factor.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs") / "gradient_metasurface")
    parser.add_argument("--no-center-aligned", dest="center_aligned", action="store_false", default=True, help="Create right trapezoid (bottom-aligned) instead of isosceles trapezoid (default).")
    parser.add_argument("--preview-crop-fraction", type=float, default=0.1, help="Center crop fraction used only for PNG preview.")
    parser.add_argument("--preview-pixels-per-unit", type=float, default=12.0, help="Pixels per um for PNG preview scaling.")
    parser.add_argument("--preview-max-total-pixels", type=int, default=4_000_000, help="Maximum total pixels allowed for preview output.")
    return parser


def run_gradient_demo(
    *,
    layout_width_um: float = 1000.0,
    layout_height_um: float = 1000.0,
    rows: int | None = None,
    cols: int | None = None,
    pitch_min_um: float = 0.84,
    pitch_max_um: float = 0.93,
    fill_min: float = 0.54,
    fill_max: float = 0.62,
    tri_factor: float = 0.05,
    output_dir: Path = Path("outputs") / "gradient_metasurface",
    center_aligned: bool = True,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 12.0,
    preview_max_total_pixels: int = 4_000_000,
) -> GradientDemoResult:
    """Generate a gradient metasurface layout and cropped preview image."""

    derived_rows = rows if rows is not None else _derive_grid_dimension(layout_height_um, pitch_min_um, pitch_max_um)
    derived_cols = cols if cols is not None else _derive_grid_dimension(layout_width_um, pitch_min_um, pitch_max_um)

    spec = TrapezoidalGradientMetasurfaceSpec(
        rows=derived_rows,
        cols=derived_cols,
        pitch_min_um=pitch_min_um,
        pitch_max_um=pitch_max_um,
        fill_min=fill_min,
        fill_max=fill_max,
        tri_factor=tri_factor,
        center_aligned=center_aligned,
    )

    result = build_trapezoidal_gradient_metasurface_layout(spec)
    gds_path = output_dir / "gradient_metasurface.gds"
    png_path = output_dir / "gradient_metasurface.png"
    written_gds, written_png = save_trapezoidal_gradient_layout_files(
        result,
        gds_path,
        png_path,
        preview_crop_fraction=preview_crop_fraction,
        preview_pixels_per_unit=preview_pixels_per_unit,
        preview_max_total_pixels=preview_max_total_pixels,
    )

    loaded = load_gds(written_gds)
    summary = top_cell_summary(loaded)
    return GradientDemoResult(
        spec=spec,
        x_extent_um=result.x_extent_um,
        y_extent_um=result.y_extent_um,
        gds_path=written_gds,
        png_path=written_png,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> None:
    """Generate a gradient GDS layout, preview PNG, and print summary info."""

    parser = build_parser()
    args = parser.parse_args(argv)

    run_result = run_gradient_demo(
        layout_width_um=args.layout_width_um,
        layout_height_um=args.layout_height_um,
        rows=args.rows,
        cols=args.cols,
        pitch_min_um=args.pitch_min_um,
        pitch_max_um=args.pitch_max_um,
        fill_min=args.fill_min,
        fill_max=args.fill_max,
        tri_factor=args.tri_factor,
        output_dir=args.output_dir,
        center_aligned=args.center_aligned,
        preview_crop_fraction=args.preview_crop_fraction,
        preview_pixels_per_unit=args.preview_pixels_per_unit,
        preview_max_total_pixels=args.preview_max_total_pixels,
    )

    spec = run_result.spec

    print("Gradient metasurface generation complete")
    print(f"Rows: {spec.rows}, cols: {spec.cols}")
    print(f"P range: {spec.pitch_min_um:.3f} to {spec.pitch_max_um:.3f} um")
    print(f"Fill range: {spec.fill_min:.3f} to {spec.fill_max:.3f}")
    print(f"Tri-factor: {spec.tri_factor:.3f}")
    print(f"Estimated x extent: {run_result.x_extent_um:.2f} um")
    print(f"Estimated y extent: {run_result.y_extent_um:.2f} um")
    print(f"Wrote GDS: {run_result.gds_path}")
    print(f"Wrote preview: {run_result.png_path}")
    for item in run_result.summary:
        print(f"Top cell: {item['name']}")
        print(f"Bounding box: {item['bbox']}")
        print(f"References: {item['reference_count']}, polygons: {item['polygon_count']}")


if __name__ == "__main__":
    main()


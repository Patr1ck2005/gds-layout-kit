"""Executable demo for the grating gradient example."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from .grating import (
    GratingGradientSpec,
    build_grating_gradient_layout,
    save_grating_gradient_layout_files,
)
from .io import load_gds, top_cell_summary

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "outputs" / "grating_gradient"


@dataclass(frozen=True)
class GratingDemoResult:
    spec: GratingGradientSpec
    x_extent_um: float
    y_extent_um: float
    gds_path: Path
    png_path: Path
    grid_gds_path: Path | None
    summary: list[dict[str, object]]


def _derive_grid_dimension(layout_um: float, pitch_min_um: float, pitch_max_um: float) -> int:
    mean_pitch = (pitch_min_um + pitch_max_um) / 2.0
    return max(2, int(round(layout_um / mean_pitch)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a grating gradient GDS and PNG preview.")
    parser.add_argument("--layout-width-um", type=float, default=2000.0, help="Target layout width in um.")
    parser.add_argument("--layout-height-um", type=float, default=400.0, help="Target layout height in um.")
    parser.add_argument("--rows", type=int, default=None, help="Number of rows.")
    parser.add_argument("--cols", type=int, default=None, help="Number of columns.")
    parser.add_argument("--pitch-min-um", type=float, default=0.4, help="Minimum period in um (500 nm).")
    parser.add_argument("--pitch-max-um", type=float, default=0.7, help="Maximum period in um (600 nm).")
    parser.add_argument("--dc-min", type=float, default=0.3, help="Minimum duty cycle.")
    parser.add_argument("--dc-max", type=float, default=0.7, help="Maximum duty cycle.")
    parser.add_argument("--tone", type=str, default="positive", choices=["positive", "negative"], help="Resist tone.")
    parser.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT_DIR)
    parser.add_argument("--no-rectangular", dest="rectangular", action="store_false", default=True, help="Apply trapezoidal envelope transform instead of plain rectangular array.")
    parser.add_argument("--no-center-aligned", dest="center_aligned", action="store_false", default=True, help="Use right trapezoid instead of isosceles (only with --no-rectangular).")
    parser.add_argument("--preview-crop-fraction", type=float, default=0.1, help="Center crop fraction for PNG preview.")
    parser.add_argument("--preview-pixels-per-unit", type=float, default=128.0, help="Pixels per um for PNG preview.")
    parser.add_argument("--preview-max-total-pixels", type=int, default=4_000_000, help="Max total pixels for preview.")
    parser.add_argument("--preview-edgecolor", type=str, default="none", help="Polygon edge color for preview (default 'none' = no borders).")
    parser.add_argument("--show-grid", action="store_true", default=False, help="Overlay grid reference lines.")
    parser.add_argument("--bias-um", type=float, default=0.0, help="Global feature-width compensation in um.")
    return parser


def run_grating_demo(
    *,
    layout_width_um: float = 2000.0,
    layout_height_um: float = 400.0,
    rows: int | None = None,
    cols: int | None = None,
    pitch_min_um: float = 0.4,
    pitch_max_um: float = 0.7,
    dc_min: float = 0.3,
    dc_max: float = 0.7,
    tone: str = "positive",
    output_dir: Path = _DEFAULT_OUTPUT_DIR,
    rectangular: bool = True,
    center_aligned: bool = True,
    preview_crop_fraction: float = 0.2,
    preview_pixels_per_unit: float = 128.0,
    preview_max_total_pixels: int = 4_000_000,
    preview_edgecolor: str = "none",
    show_grid: bool = False,
    bias_um: float = 0.0,
) -> GratingDemoResult:
    derived_rows = rows if rows is not None else _derive_grid_dimension(layout_height_um, pitch_min_um, pitch_max_um)
    derived_cols = cols if cols is not None else _derive_grid_dimension(layout_width_um, pitch_min_um, pitch_max_um)

    spec = GratingGradientSpec(
        rows=derived_rows,
        cols=derived_cols,
        pitch_min_um=pitch_min_um,
        pitch_max_um=pitch_max_um,
        dc_min=dc_min,
        dc_max=dc_max,
        tone=tone,
        rectangular=rectangular,
        center_aligned=center_aligned,
        show_grid=show_grid,
        bias_um=bias_um,
    )

    result = build_grating_gradient_layout(spec)
    gds_path = output_dir / "grating_gradient.gds"
    png_path = output_dir / "grating_gradient.png"
    written_gds, written_png, written_grid = save_grating_gradient_layout_files(
        result,
        gds_path,
        png_path,
        preview_crop_fraction=preview_crop_fraction,
        preview_pixels_per_unit=preview_pixels_per_unit,
        preview_max_total_pixels=preview_max_total_pixels,
        preview_edgecolor=preview_edgecolor,
    )

    loaded = load_gds(written_gds)
    summary = top_cell_summary(loaded)
    return GratingDemoResult(
        spec=spec,
        x_extent_um=result.x_extent_um,
        y_extent_um=result.y_extent_um,
        gds_path=written_gds,
        png_path=written_png,
        grid_gds_path=written_grid,
        summary=summary,
    )


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    run_result = run_grating_demo(
        layout_width_um=args.layout_width_um,
        layout_height_um=args.layout_height_um,
        rows=args.rows,
        cols=args.cols,
        pitch_min_um=args.pitch_min_um,
        pitch_max_um=args.pitch_max_um,
        dc_min=args.dc_min,
        dc_max=args.dc_max,
        tone=args.tone,
        output_dir=args.output_dir,
        rectangular=args.rectangular,
        center_aligned=args.center_aligned,
        preview_crop_fraction=args.preview_crop_fraction,
        preview_pixels_per_unit=args.preview_pixels_per_unit,
        preview_max_total_pixels=args.preview_max_total_pixels,
        preview_edgecolor=args.preview_edgecolor,
        show_grid=args.show_grid,
        bias_um=args.bias_um,
    )

    spec = run_result.spec

    print("Grating gradient generation complete")
    print(f"Rows: {spec.rows}, cols: {spec.cols}")
    print(f"Period range: {spec.pitch_min_um:.3f} to {spec.pitch_max_um:.3f} um")
    print(f"DC range: {spec.dc_min:.3f} to {spec.dc_max:.3f}")
    print(f"Tone: {spec.tone}")
    print(f"Estimated x extent: {run_result.x_extent_um:.2f} um")
    print(f"Estimated y extent: {run_result.y_extent_um:.2f} um")
    print(f"Wrote GDS: {run_result.gds_path}")
    if run_result.grid_gds_path is not None:
        print(f"Wrote grid-only GDS: {run_result.grid_gds_path}")
    print(f"Wrote preview: {run_result.png_path}")
    for item in run_result.summary:
        print(f"Top cell: {item['name']}")
        print(f"Bounding box: {item['bbox']}")
        print(f"References: {item['reference_count']}, polygons: {item['polygon_count']}")


if __name__ == "__main__":
    main()

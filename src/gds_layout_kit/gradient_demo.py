"""Executable demo for the gradient metasurface example."""

from __future__ import annotations

import argparse
from pathlib import Path

from .io import load_gds, top_cell_summary
from .metasurface import GradientMetasurfaceSpec, build_gradient_metasurface_layout, save_gradient_layout_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a gradient photonic metasurface GDS and PNG preview.")
    parser.add_argument("--rows", type=int, default=160, help="Number of rows in the preview layout.")
    parser.add_argument("--cols", type=int, default=220, help="Number of columns in the preview layout.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs") / "gradient_metasurface")
    parser.add_argument("--top-scale", type=float, default=0.92, help="Row-wise x scale at the top edge of the trapezoid.")
    parser.add_argument("--bottom-scale", type=float, default=1.0, help="Row-wise x scale at the bottom edge of the trapezoid.")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Generate a gradient GDS layout, preview PNG, and print summary info."""

    parser = build_parser()
    args = parser.parse_args(argv)

    spec = GradientMetasurfaceSpec(
        rows=args.rows,
        cols=args.cols,
        trapezoid_bottom_scale=args.bottom_scale,
        trapezoid_top_scale=args.top_scale,
    )

    result = build_gradient_metasurface_layout(spec)
    output_dir: Path = args.output_dir
    gds_path = output_dir / "gradient_metasurface.gds"
    png_path = output_dir / "gradient_metasurface.png"
    written_gds, written_png = save_gradient_layout_files(result, gds_path, png_path)

    loaded = load_gds(written_gds)
    summary = top_cell_summary(loaded)

    print("Gradient metasurface generation complete")
    print(f"Rows: {spec.rows}, cols: {spec.cols}")
    print(f"P range: {spec.pitch_min_um:.3f} to {spec.pitch_max_um:.3f} um")
    print(f"Fill range: {spec.fill_min:.3f} to {spec.fill_max:.3f}")
    print(f"Tri-factor: {spec.tri_factor:.3f}")
    print(f"Estimated x extent: {result.x_extent_um:.2f} um")
    print(f"Estimated y extent: {result.y_extent_um:.2f} um")
    print(f"Wrote GDS: {written_gds}")
    print(f"Wrote preview: {written_png}")
    for item in summary:
        print(f"Top cell: {item['name']}")
        print(f"Bounding box: {item['bbox']}")
        print(f"References: {item['reference_count']}, polygons: {item['polygon_count']}")


if __name__ == "__main__":
    main()


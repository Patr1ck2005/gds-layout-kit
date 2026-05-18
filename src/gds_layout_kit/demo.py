"""Executable demo for the minimal GDS layout kit."""

from __future__ import annotations

from pathlib import Path

from .assembly import build_demo_layout
from .io import load_gds, top_cell_summary, write_gds
from .preview import save_cell_preview


def main() -> None:
    """Generate a demo GDS layout, a preview PNG, and print summary info."""

    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / "outputs"
    gds_path = output_dir / "demo_layout.gds"
    png_path = output_dir / "demo_layout.png"

    library, cells = build_demo_layout()
    write_gds(library, gds_path)
    save_cell_preview(cells.top, png_path)

    loaded = load_gds(gds_path)
    summary = top_cell_summary(loaded)

    print(f"Wrote GDS: {gds_path}")
    print(f"Wrote preview: {png_path}")
    for item in summary:
        print(f"Top cell: {item['name']}")
        print(f"Bounding box: {item['bbox']}")
        print(f"References: {item['reference_count']}, polygons: {item['polygon_count']}")


if __name__ == "__main__":
    main()


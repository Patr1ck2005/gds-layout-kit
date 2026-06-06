from __future__ import annotations

from pathlib import Path

from gds_layout_kit.gradient_demo import run_gradient_demo

params = dict(
    layout_width_um=10.0,
    layout_height_um=10.0,
    rows=None,
    cols=None,
    pitch_min_um=0.42,
    pitch_max_um=0.93,
    fill_min=0.54,
    fill_max=0.62,
    tri_factor=0.05,
    output_dir=Path("outputs/gradient_metasurface"),
    center_aligned=True,
    preview_crop_fraction=0.1,
    preview_pixels_per_unit=12.0,
    preview_max_total_pixels=4_000_000,
)

if __name__ == "__main__":
    run_gradient_demo(**params)


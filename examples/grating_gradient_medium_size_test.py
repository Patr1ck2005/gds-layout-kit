from __future__ import annotations

from pathlib import Path

from gds_layout_kit.grating_demo import run_grating_demo

params = dict(
    layout_width_um=500.0,
    layout_height_um=200.0,
    rows=None,
    cols=None,
    pitch_min_um=0.4,
    pitch_max_um=0.7,
    dc_min=0.3,
    dc_max=0.7,
    bias_um=-0.020,
    tone="positive",
    output_dir=Path("outputs/grating_gradient"),
    rectangular=True,
    center_aligned=True,
    preview_crop_fraction=0.1,
    preview_pixels_per_unit=128.0,
    preview_max_total_pixels=4_000_000,
    preview_edgecolor="none",
    show_grid=False,
)

if __name__ == "__main__":
    run_grating_demo(**params)

"""Minimal GDS layout generation toolkit."""

from .assembly import build_demo_layout
from .io import load_gds, top_cell_summary, write_gds
from .metasurface import (
    GradientMetasurfaceSpec,
    GradientMetasurfaceSpecBase,
    GradientMetasurfaceResult,
    TrapezoidalGradientMetasurfaceSpec,
    build_gradient_metasurface_layout,
    build_trapezoidal_gradient_metasurface_layout,
    save_gradient_layout_files,
    save_trapezoidal_gradient_layout_files,
)
from .preview import save_cell_preview
from .primitives import (
    make_alignment_marker_cell,
    make_label_cell,
    make_metal_block_cell,
    make_pad_cell,
    make_ring_cell,
)
from .transform import (
    TrapezoidalGradientTransform,
    apply_transform_to_polygons,
    compute_trapezoid_extents,
)

__all__ = [
    "build_demo_layout",
    "load_gds",
    "top_cell_summary",
    "write_gds",
    "GradientMetasurfaceSpecBase",
    "TrapezoidalGradientMetasurfaceSpec",
    "GradientMetasurfaceSpec",
    "GradientMetasurfaceResult",
    "build_trapezoidal_gradient_metasurface_layout",
    "build_gradient_metasurface_layout",
    "save_trapezoidal_gradient_layout_files",
    "save_gradient_layout_files",
    "TrapezoidalGradientTransform",
    "apply_transform_to_polygons",
    "compute_trapezoid_extents",
    "make_alignment_marker_cell",
    "make_label_cell",
    "make_metal_block_cell",
    "make_pad_cell",
    "make_ring_cell",
    "save_cell_preview",
]


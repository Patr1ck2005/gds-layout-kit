"""Coordinate transformation framework for gradient metasurfaces.

The core idea: generate patterns in a uniform rectangular grid, then apply
a global smooth coordinate transformation to warp the entire layout.  This
separates "what patterns look like" from "where they go and how they stretch."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


Point2D = tuple[float, float]
Polygon = list[Point2D]


class CoordinateTransform(Protocol):
    """Protocol for a 2D coordinate transformation."""

    def transform_point(self, x: float, y: float) -> Point2D: ...


@dataclass(frozen=True)
class TrapezoidalGradientTransform:
    """Smooth coordinate transform for trapezoidal gradient metasurfaces.

    Maps a uniform rectangular grid (spacing P_0 x P_0) to a trapezoidal
    gradient grid where the local period varies from *pitch_min_um* to
    *pitch_max_um* along the x-axis.

    The x-transformation is a nonlinear warp (quadratic) so that patterns
    are subtly distorted -- left and right edges stretch by different amounts.
    The y-transformation preserves the trapezoid shape with optional centre
    alignment.

    Parameters
    ----------
    pitch_min_um:
        Minimum local period in um (leftmost column).
    pitch_max_um:
        Maximum local period in um (rightmost column).
    base_period_um:
        Period used in the uniform reference grid.  Defaults to *pitch_min_um*
        so the narrowest column maps 1:1.
    num_cols: Number of columns in the grid.
    num_rows: Number of rows (needed for centre-alignment offset).
    center_aligned:
        If True, produce an isosceles trapezoid; if False, a right trapezoid
        with the bottom row aligned.
    """

    pitch_min_um: float
    pitch_max_um: float
    base_period_um: float
    num_cols: int
    num_rows: int
    center_aligned: bool = True

    def __post_init__(self) -> None:
        if self.pitch_min_um <= 0 or self.pitch_max_um <= 0:
            raise ValueError("pitch values must be positive")
        if self.pitch_max_um < self.pitch_min_um:
            raise ValueError("pitch_max_um must be >= pitch_min_um")
        if self.base_period_um <= 0:
            raise ValueError("base_period_um must be positive")
        if self.num_cols < 2:
            raise ValueError("num_cols must be at least 2")
        if self.num_rows < 2:
            raise ValueError("num_rows must be at least 2")

        delta_p = self.pitch_max_um - self.pitch_min_um
        L = self.num_cols * self.base_period_um
        A = self.pitch_min_um / self.base_period_um
        B = delta_p / (2.0 * L * self.base_period_um)
        offset_c = -(self.num_rows / 2.0) * delta_p / L if self.center_aligned else 0.0

        # Use object.__setattr__ to work around frozen=True
        object.__setattr__(self, "_a", A)
        object.__setattr__(self, "_b", B)
        object.__setattr__(self, "_offset_c", offset_c)
        object.__setattr__(self, "_L", L)

    def transform_point(self, x: float, y: float) -> Point2D:
        """Map a single point from uniform grid to gradient grid."""
        a = self._a  # type: ignore[attr-defined]
        b = self._b  # type: ignore[attr-defined]
        c = self._offset_c  # type: ignore[attr-defined]

        x_prime = a * x + b * x * x
        y_scale = a + 2.0 * b * x
        y_prime = y * y_scale + c * x
        return (x_prime, y_prime)


def apply_transform_to_polygons(
    polygons: list[Polygon],
    transform: CoordinateTransform,
) -> list[Polygon]:
    """Return a new list of polygons with every vertex transformed.

    Does not mutate the input lists.
    """
    return [
        [transform.transform_point(px, py) for (px, py) in poly]
        for poly in polygons
    ]


def compute_trapezoid_extents(
    *,
    pitch_min_um: float,
    pitch_max_um: float,
    num_cols: int,
    num_rows: int,
    center_aligned: bool = True,
) -> tuple[float, float]:
    """Return analytical (x_extent_um, y_extent_um) for a trapezoidal layout.

    These are edge-to-edge extents (not centre-to-centre).
    """
    delta_p = pitch_max_um - pitch_min_um
    x_extent_um = num_cols * (pitch_min_um + pitch_max_um) / 2.0

    if center_aligned:
        y_extent_um = num_rows * pitch_max_um
    else:
        y_extent_um = num_rows * pitch_max_um

    return x_extent_um, y_extent_um

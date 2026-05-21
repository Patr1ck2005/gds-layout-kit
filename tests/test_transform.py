from __future__ import annotations

import math

import pytest

from gds_layout_kit.transform import (
    TrapezoidalGradientTransform,
    apply_transform_to_polygons,
    compute_trapezoid_extents,
)


def _make_transform(**overrides):
    defaults = dict(
        pitch_min_um=0.84,
        pitch_max_um=0.93,
        base_period_um=0.84,
        num_cols=10,
        num_rows=8,
        center_aligned=True,
    )
    defaults.update(overrides)
    return TrapezoidalGradientTransform(**defaults)


class TestTrapezoidalGradientTransform:
    def test_identity_when_zero_gradient(self):
        t = _make_transform(pitch_min_um=1.0, pitch_max_um=1.0, base_period_um=1.0)
        for x, y in [(0, 0), (5.0, 3.0), (10.0, 8.0)]:
            xp, yp = t.transform_point(x, y)
            assert xp == pytest.approx(x)
            assert yp == pytest.approx(y)

    def test_x_prime_zero_at_origin(self):
        t = _make_transform()
        xp, _ = t.transform_point(0.0, 0.0)
        assert xp == pytest.approx(0.0)

    def test_x_prime_at_end_matches_analytical(self):
        t = _make_transform(num_cols=10, base_period_um=1.0,
                            pitch_min_um=0.5, pitch_max_um=1.5)
        L = 10 * 1.0  # num_cols * base_period
        xp, _ = t.transform_point(L, 0.0)
        expected = 10 * (0.5 + 1.5) / 2.0  # cols * avg_pitch
        assert xp == pytest.approx(expected)

    def test_center_row_constant_y_across_x(self):
        t = _make_transform(num_rows=8, base_period_um=1.0, center_aligned=True)
        y_center = 8 * 1.0 / 2.0  # rows * P0 / 2
        target = 8 * 0.84 / 2.0  # rows * pitch_min / 2
        L = 10 * 1.0
        for x in [0.0, L * 0.25, L * 0.5, L * 0.75, L]:
            _, yp = t.transform_point(x, y_center)
            assert yp == pytest.approx(target, rel=1e-9)

    def test_bottom_row_always_zero_when_bottom_aligned(self):
        t = _make_transform(center_aligned=False)
        L = 10 * 0.84  # num_cols * base_period
        for x in [0.0, L * 0.3, L * 0.7, L]:
            _, yp = t.transform_point(x, 0.0)
            assert yp == pytest.approx(0.0, abs=1e-12)

    def test_x_prime_monotonic(self):
        t = _make_transform()
        L = 10 * 0.84
        prev = -1.0
        for x in [0.0, L * 0.2, L * 0.5, L * 0.8, L]:
            xp, _ = t.transform_point(x, 0.0)
            assert xp > prev
            prev = xp

    def test_y_scale_increases_with_x_bottom_aligned(self):
        """With bottom alignment, y' grows with x because y_scale(x) grows."""
        t = _make_transform(center_aligned=False)
        L = 10 * 0.84
        _, y0 = t.transform_point(0.0, 1.0)
        _, y1 = t.transform_point(L, 1.0)
        assert y1 > y0

    def test_center_aligned_bottom_half_shifts_downward(self):
        """Below the center row, points shift downward at larger x."""
        t = _make_transform(num_rows=8, base_period_um=1.0, center_aligned=True)
        L = 10 * 0.84
        y_center = 8 * 1.0 / 2.0  # = 4.0
        # At y below center, offset dominates and y' decreases with x
        _, y_below_0 = t.transform_point(0.0, y_center * 0.25)  # at 1/4 center height
        _, y_below_L = t.transform_point(L, y_center * 0.25)
        assert y_below_L < y_below_0

    def test_trapezoid_symmetry_center_aligned(self):
        """Top and bottom rows should be symmetric around the center y."""
        t = _make_transform(num_rows=8, base_period_um=1.0, center_aligned=True)
        y_center = 8 * 1.0 / 2.0
        L = 10 * 1.0
        for x in [0.0, L * 0.5, L]:
            _, yc = t.transform_point(x, y_center)
            _, y_top = t.transform_point(x, 8.0)
            _, y_bot = t.transform_point(x, 0.0)
            assert (y_top - yc) == pytest.approx(yc - y_bot, rel=1e-9)


class TestValidation:
    def test_negative_pitch_min_raises(self):
        with pytest.raises(ValueError):
            _make_transform(pitch_min_um=-0.1)

    def test_zero_pitch_raises(self):
        with pytest.raises(ValueError):
            _make_transform(pitch_min_um=0.0)

    def test_pitch_max_less_than_min_raises(self):
        with pytest.raises(ValueError):
            _make_transform(pitch_min_um=1.0, pitch_max_um=0.5)

    def test_zero_base_period_raises(self):
        with pytest.raises(ValueError):
            _make_transform(base_period_um=0.0)

    def test_single_column_raises(self):
        with pytest.raises(ValueError):
            _make_transform(num_cols=1)

    def test_single_row_raises(self):
        with pytest.raises(ValueError):
            _make_transform(num_rows=1)


class TestApplyTransformToPolygons:
    def test_empty_list_returns_empty(self):
        result = apply_transform_to_polygons([], _make_transform())
        assert result == []

    def test_does_not_mutate_input(self):
        t = _make_transform()
        poly = [[(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]]
        original = [[(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]]
        apply_transform_to_polygons(poly, t)
        assert poly == original

    def test_transforms_all_vertices(self):
        t = _make_transform(pitch_min_um=1.0, pitch_max_um=1.0, base_period_um=1.0)
        poly = [[(1.0, 2.0), (3.0, 4.0)]]
        result = apply_transform_to_polygons(poly, t)
        assert len(result) == 1
        assert len(result[0]) == 2
        # identity transform
        assert result[0][0] == pytest.approx((1.0, 2.0))
        assert result[0][1] == pytest.approx((3.0, 4.0))

    def test_multiple_polygons(self):
        t = _make_transform()
        polys = [[(0.0, 0.0)], [(1.0, 1.0)], [(2.0, 2.0)]]
        result = apply_transform_to_polygons(polys, t)
        assert len(result) == 3


class TestComputeTrapezoidExtents:
    def test_x_extent_analytical(self):
        x_ext, _ = compute_trapezoid_extents(
            pitch_min_um=0.5, pitch_max_um=1.5,
            num_cols=20, num_rows=10,
        )
        assert x_ext == pytest.approx(20 * (0.5 + 1.5) / 2.0)

    def test_y_extent_center_aligned(self):
        _, y_ext = compute_trapezoid_extents(
            pitch_min_um=0.84, pitch_max_um=0.93,
            num_cols=220, num_rows=160, center_aligned=True,
        )
        assert y_ext == pytest.approx(160 * 0.93)

    def test_y_extent_bottom_aligned(self):
        _, y_ext = compute_trapezoid_extents(
            pitch_min_um=0.84, pitch_max_um=0.93,
            num_cols=220, num_rows=160, center_aligned=False,
        )
        assert y_ext == pytest.approx(160 * 0.93)

    def test_zero_gradient_y_extent(self):
        _, y_ext = compute_trapezoid_extents(
            pitch_min_um=1.0, pitch_max_um=1.0,
            num_cols=10, num_rows=5,
        )
        assert y_ext == pytest.approx(5.0)

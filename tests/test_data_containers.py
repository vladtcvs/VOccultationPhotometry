import pytest
import numpy as np
import cv2
from voccultation.data_structures.data_containers import (
    DriftTrackRect,
    DriftTrackPath,
    DriftTrack,
    DriftSlice,
    DriftProfile,
)


class TestDriftTrackRect:
    def test_init_valid(self):
        rect = DriftTrackRect(0, 10, 0, 10)
        assert rect.left == 0
        assert rect.right == 10
        assert rect.top == 0
        assert rect.bottom == 10
        assert rect.w == 11
        assert rect.h == 11

    def test_init_invalid_right_less_left(self):
        with pytest.raises(AssertionError):
            DriftTrackRect(10, 0, 0, 10)

    def test_init_invalid_bottom_less_top(self):
        with pytest.raises(AssertionError):
            DriftTrackRect(0, 10, 10, 0)

    def test_point_inside_rect(self):
        rect = DriftTrackRect(0, 10, 0, 10)
        assert rect.point_inside_rect(5, 5) is True
        assert rect.point_inside_rect(0, 0) is True
        assert rect.point_inside_rect(10, 10) is True
        assert rect.point_inside_rect(-1, 5) is False
        assert rect.point_inside_rect(5, -1) is False
        assert rect.point_inside_rect(11, 5) is False
        assert rect.point_inside_rect(5, 11) is False

    def test_detect_overlap(self):
        rect1 = DriftTrackRect(0, 10, 0, 10)
        rect2 = DriftTrackRect(5, 15, 5, 15)  # overlaps
        rect3 = DriftTrackRect(20, 30, 20, 30)  # no overlap
        assert rect1.detect_overlap(rect2) is True
        assert rect1.detect_overlap(rect3) is False

    def test_extract_track(self):
        gray = np.random.rand(20, 20).astype(np.float32)
        rect = DriftTrackRect(5, 10, 5, 10)
        track, mask = rect.extract_track(gray, 2)
        assert track.shape == (10, 10)  # w+2*margin, h+2*margin
        assert mask.shape == (10, 10)
        # Check that mask is 1 where data is present
        assert np.all(mask[2:7, 2:7] == 1)  # Inside the original rect


class TestDriftTrackPath:
    def test_init_valid(self):
        points = np.array([[0, 0], [1, 1]])
        normals = np.array([[0, 1], [1, 0]])
        path = DriftTrackPath(points, normals, 5.0)
        assert np.array_equal(path.points, points)
        assert np.array_equal(path.normals, normals)
        assert path.half_w == 5.0
        assert path.length == 2

    def test_init_invalid_points_shape(self):
        with pytest.raises(AssertionError):
            DriftTrackPath(np.array([0, 1]), None, 5.0)

    def test_init_invalid_normals_shape(self):
        points = np.array([[0, 0], [1, 1]])
        normals = np.array([0, 1])  # Wrong shape
        with pytest.raises(AssertionError):
            DriftTrackPath(points, normals, 5.0)

    def test_init_negative_half_w(self):
        points = np.array([[0, 0]])
        with pytest.raises(AssertionError):
            DriftTrackPath(points, None, -1.0)


class TestDriftTrack:
    def test_init_valid(self):
        gray = np.random.rand(10, 10).astype(np.float32)
        path = DriftTrackPath(np.array([[0, 0]]), None, 5.0)
        track = DriftTrack(gray, 2, path)
        assert np.array_equal(track.gray, gray)
        assert track.margin == 2
        assert track.path == path
        assert track.w == 6  # 10 - 2*2
        assert track.h == 6

    def test_init_invalid_gray_shape(self):
        with pytest.raises(AssertionError):
            DriftTrack(np.array([1, 2]), 0, None)

    def test_init_negative_margin(self):
        gray = np.random.rand(10, 10)
        path = DriftTrackPath(np.array([[0, 0]]), None, 5.0)
        with pytest.raises(AssertionError):
            DriftTrack(gray, -1, path)

    def test_draw(self):
        gray = np.zeros((10, 10), dtype=np.uint8)
        path = DriftTrackPath(np.array([[5, 5]]), np.array([[0, 1]]), 5.0)
        track = DriftTrack(gray, 0, path)
        rgb = track.draw((255, 0, 0),  (0,200,0), 0.5)
        assert rgb.shape == (10, 10, 3)
        assert rgb.dtype == np.uint8

    def test_draw_in_place(self):
        rgb = np.zeros((10, 10, 3), dtype=np.uint8)
        path = DriftTrackPath(np.array([[5, 5]]), np.array([[0, 1]]), 5.0)
        track = DriftTrack(np.zeros((10, 10), dtype=np.uint8), 0, path)
        track.draw_in_place(rgb, 0, 0, (255, 0, 0),  (0,200,0), 0.5)
        # Check that color was applied (rough check)
        print(rgb[5,:,:])
        assert rgb[5, 5, 1] > 0  # Green channel


class TestDriftSlice:
    def test_init_valid(self):
        slices = np.random.rand(10, 20).astype(np.float32)
        ds = DriftSlice(slices)
        assert np.array_equal(ds.slices, slices)
        assert ds.length == 10
        assert ds.width == 20
        assert ds.mask.shape == (10, 20)

    def test_init_invalid_shape(self):
        with pytest.raises(AssertionError):
            DriftSlice(np.array([1, 2, 3]))

    def test_draw(self):
        slices = np.random.rand(10, 20).astype(np.float32) * 255
        ds = DriftSlice(slices)
        rgb, _ = ds.draw(5)
        assert rgb.shape == (20, 10, 3)  # Transposed

    def test_plot_slice(self):
        slices = np.random.rand(10, 20).astype(np.float32)
        ds = DriftSlice(slices)
        rgb = ds.plot_slice(100, 100, 5)
        assert rgb.shape == (100, 100, 3)

    def test_plot_slices(self):
        slices = np.random.rand(10, 20).astype(np.float32)
        ds = DriftSlice(slices)
        rgb = ds.plot_slices(100, 100)
        assert rgb.shape == (100, 100, 3)

class TestDriftProfile:
    def test_init_valid(self):
        profile = np.random.rand(10).astype(np.float32)
        error = np.random.rand(10).astype(np.float32)
        dp = DriftProfile(profile, error)
        assert np.array_equal(dp.profile, profile)
        assert np.array_equal(dp.error, error)
        assert dp.length == 10

    def test_init_no_error(self):
        profile = np.random.rand(10)
        dp = DriftProfile(profile, None)
        assert np.all(dp.error == 0)

    def test_init_invalid_profile_shape(self):
        with pytest.raises(AssertionError):
            DriftProfile(np.array([[1, 2], [3, 4]]), None)

    def test_plot_profile(self):
        profile = np.random.rand(10)
        dp = DriftProfile(profile, None)
        rgb = dp.plot_profile(100, 100)
        assert rgb.shape == (100, 100, 3)

    def test_plot_profile_with_error(self):
        profile = np.random.rand(10)
        error = np.random.rand(10)
        dp = DriftProfile(profile, error)
        rgb = dp.plot_profile_with_error(100, 100)
        assert rgb.shape == (100, 100, 3)
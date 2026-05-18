#
# Copyright (c) 2026 Vladislav Tsendrovskii
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

"""Data containers for drift track analysis in voccultation.

Defines rectangular regions (DriftTrackRect), paths (DriftTrackPath),
tracks (DriftTrack), extracted slices (DriftSlice), and profiles (DriftProfile)
for processing star drift tracks in images.
"""

from typing import Tuple
import numpy as np
import cv2

from voccultation.model.plot import plot_to_numpy

class DriftTrackRect:
    """
    Represents a rectangular region of interest on an image.

    Attributes:
        left (int): The x-coordinate of the left edge of the rectangle.
        right (int): The x-coordinate of the right edge of the rectangle.
        top (int): The y-coordinate of the top edge of the rectangle.
        bottom (int): The y-coordinate of the bottom edge of the rectangle.

    Methods:
        point_inside_rect(x, y) -> bool: Check if a point is inside the rectangle.
        detect_overlap(other) -> bool: Detect overlap with another rectangle.
        extract_track(gray, margin) -> Tuple[np.ndarray, np.ndarray]: Extract a track from an image.
    """
    def __init__(self, left : int, right : int, top : int, bottom : int):
        """
        Initialize a DriftTrackRect with the given coordinates.

        Args:
            left (int): The x-coordinate of the left edge.
            right (int): The x-coordinate of the right edge.
            top (int): The y-coordinate of the top edge.
            bottom (int): The y-coordinate of the bottom edge.
        """
        assert right > left, "right must be greater than left"
        assert bottom > top, "bottom must be greater than top"

        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.w = self.right - self.left + 1
        self.h = self.bottom - self.top + 1

    def point_inside_rect(self, x : int, y : int) -> bool:
        """
        Check if a point is inside the rectangle.

        Args:
            x (int): The x-coordinate of the point.
            y (int): The y-coordinate of the point.

        Returns:
            bool: True if the point is inside the rectangle, False otherwise.
        """
        return x >= self.left and x <= self.right and y >= self.top and y <= self.bottom

    def specify_position(self, x : int, y : int):
        """
        Set the position of the rectangle while preserving its size.

        Args:
            x (int): The new x-coordinate of the left edge.
            y (int): The new y-coordinate of the top edge.
        """
        self.left = x
        self.top = y
        self.right = self.left + self.w - 1
        self.bottom = self.top + self.h - 1

    def specify_size(self, w : int, h : int):
        """
        Set the size of the rectangle while preserving its position.

        Args:
            w (int): The new width of the rectangle.
            h (int): The new height of the rectangle.
        """
        self.w = w
        self.h = h
        self.right = self.left + self.w - 1
        self.bottom = self.top + self.h - 1

    def detect_overlap(self, other) -> bool:
        """
        Detect overlap with another rectangle.

        Args:
            other (DriftTrackRect): The other rectangle to check for overlap.

        Returns:
            bool: True if there is overlap, False otherwise.
        """
        other_ : DriftTrackRect = other
        if self.point_inside_rect(other_.left, other_.top):
            return True
        if self.point_inside_rect(other_.right, other_.top):
            return True
        if self.point_inside_rect(other_.left, other_.bottom):
            return True
        if self.point_inside_rect(other_.right, other_.bottom):
            return True
        return False

    def extract_track(self, gray : np.ndarray, margin : int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract a track from an image with the given margin.

        Args:
            gray (np.ndarray): The input grayscale image.
            margin (int): The margin around the rectangle.

        Returns:
            Tuple[np.ndarray, np.ndarray]: The extracted track and its mask.
        """
        x0 = self.left-margin
        y0 = self.top-margin
        x1 = self.right+margin+1
        y1 = self.bottom+margin+1

        tw = x1 - x0
        th = y1 - y0

        x0_c = max(x0, 0)
        y0_c = max(y0, 0)
        x1_c = min(x1, gray.shape[1])
        y1_c = min(y1, gray.shape[0])

        dy = y0_c - y0
        dx = x0_c - x0
        cw = x1_c - x0_c
        ch = y1_c - y0_c

        result = np.empty((th, tw))
        result.fill(np.nan)
        if cw > 0 and ch > 0:
            track = gray[y0_c:y1_c, x0_c:x1_c]
            result[dy:dy+ch, dx:dx+cw] = track

        mask = np.ones(result.shape)
        idxs = np.where(np.isnan(result))
        mask[idxs] = 0
        result[idxs] = 0

        return result, mask

class DriftTrackPath:
    """
    Represents a path of points on an image.

    Attributes:
        points (np.ndarray): The points in the path. Array of pairs [(x,y)]
        normals (np.ndarray): The normals to the points.  Array of pairs [(nx,ny)]
        half_w (float): The half-width of the track.

    Methods:
        None
    """
    def __init__(self,
                 points : np.ndarray,
                 normals : np.ndarray | None,
                 half_w : int | None):
        """
        Initialize a DriftTrackPath with points, normals, and half-width.

        Args:
            points (np.ndarray): Array of points [(y, x)].
            normals (np.ndarray | None): Array of normals [(ny, nx)].
            half_w (int): Half-width of the track.
        """
        assert len(points.shape) == 2
        assert points.shape[1] == 2

        if half_w is not None:
            assert half_w >= 0

        if normals is not None:
            assert len(normals.shape) == 2
            assert normals.shape[1] == 2
            assert normals.shape[0] == points.shape[0]

        self.points = points            # points [(y, x)]
        self.normals = normals          # normals [(ny, nx)]
        self.half_w = half_w            # 1/2 width of track
        self.length = self.points.shape[0]

class DriftTrack:
    """
    Represents a track of stars on an image.

    Attributes:
        gray (np.ndarray): The image data. 2-dimensional array with gray image
        margin (int): The margin around the track.
        path (DriftTrackPath): The path of points in the track.

    Methods:
        draw(color, transparency) -> np.ndarray: Draw the track and its normals.
        draw_in_place(rgb, left, top, color, transparency) -> np.ndarray: Draw the track and its normals in place.
    """
    def __init__(self,
                 gray : np.ndarray,
                 margin : int,
                 path : DriftTrackPath):
        """
        Initialize a DriftTrack with image data, margin, and path.

        Args:
            gray (np.ndarray): The grayscale image data.
            margin (int): Margin around the track.
            path (DriftTrackPath): The path of points in the track.
        """
        assert len(gray.shape) == 2
        assert margin >= 0

        self.gray = gray                # part of image
        self.margin = margin            # margin
        self.path = path
        self.w = self.gray.shape[1]-2*self.margin
        self.h = self.gray.shape[0]-2*self.margin

    def draw(self, color : tuple, normals_color : tuple, transparency : float, zoom : int) -> np.ndarray:
        """
        Draw the track and its normals.

        Args:
            color (tuple): Color for the path.
            normals_color (tuple): Color for the normals.
            transparency (float): Transparency value.
            zoom (int): Zoom factor.

        Returns:
            np.ndarray: The RGB image with the track drawn.
        """
        gray = self.gray.astype(np.float32)
        amax = np.amax(gray)
        if amax > 0:
            gray = gray / amax * 255

        rgb = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        return self.draw_in_place(rgb, 0, 0, color, normals_color, transparency, zoom)

    def draw_in_place(self,
                      rgb : np.ndarray,
                      left : int,
                      top : int,
                      path_color : tuple,
                      normals_color : tuple,
                      transparency : float,
                      zoom : int) -> np.ndarray:
        """
        Draw the track and its normals in place on the given RGB image.

        Args:
            rgb (np.ndarray): The RGB image to draw on.
            left (int): Left offset.
            top (int): Top offset.
            path_color (tuple): Color for the path.
            normals_color (tuple): Color for the normals.
            transparency (float): Transparency value.
            zoom (int): Zoom factor.

        Returns:
            np.ndarray: The modified RGB image.
        """
        # draw points
        if self.path is not None and len(self.path.points) >= 2:
            for idx in range(len(self.path.points)-1):
                y1, x1 = self.path.points[idx]
                y2, x2 = self.path.points[idx+1]
                xx1 = int(x1 + left + self.margin)*zoom
                yy1 = int(y1 + top + self.margin)*zoom
                xx2 = int(x2 + left + self.margin)*zoom
                yy2 = int(y2 + top + self.margin)*zoom
                if xx1 < 0 or yy1 < 0 or xx1 >= rgb.shape[1] or yy1 >= rgb.shape[0]:
                    continue
                if xx2 < 0 or yy2 < 0 or xx2 >= rgb.shape[1] or yy2 >= rgb.shape[0]:
                    continue
                cv2.line(rgb, (xx1,yy1), (xx2,yy2), path_color, 1)

        # draw normals
        if self.path is not None and self.path.normals is not None:
            for index, ((y,x), (ny,nx)) in enumerate(zip(self.path.points, self.path.normals)):
                if index % 10 != 0:
                    continue
                x1 = int(x - nx*self.path.half_w + self.margin)*zoom
                y1 = int(y - ny*self.path.half_w + self.margin)*zoom
                x2 = int(x + nx*self.path.half_w + self.margin)*zoom
                y2 = int(y + ny*self.path.half_w + self.margin)*zoom

                cv2.line(rgb, (x1+left*zoom,y1+top*zoom), (x2+left*zoom,y2+top*zoom), normals_color, 1)
        return rgb

class DriftSlice:
    """
    Represents an extracted star track.

    Attributes:
        slices (np.ndarray): The sliced data.
        width (int): The width of the slice, taking into account the half width removed from each side.
        mask (np.ndarray): A mask for the sliced data.

    Methods:
        draw(used_width) -> np.ndarray: Draw the slice.
        plot_slice(w, h, layer) -> np.ndarray: Plot a single slice.
        plot_slices(w, h) -> np.ndarray: Plot multiple slices.
    """
    def __init__(self, slices : np.ndarray):
        """
        Initialize a DriftSlice with sliced data.

        Args:
            slices (np.ndarray): The 2D array of sliced data.
        """
        assert len(slices.shape) == 2

        self.slices = slices
        self.length = self.slices.shape[0]
        self.width = self.slices.shape[1]
        self.mask = 1-np.isnan(self.slices)
        self.slices[np.where(np.isnan(self.slices))] = 0

    def draw(self, used_width : int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Draw the slice with optional width markers.

        Args:
            used_width (int): The width to mark on the slice.

        Returns:
            Tuple[np.ndarray, np.ndarray]: The RGB image and marks overlay.
        """
        slices = self.slices.astype(np.float32)
        amax=np.amax(slices)
        if amax > 0:
            slices = slices / amax * 255
        rgb = cv2.cvtColor(slices.transpose().astype(np.uint8), cv2.COLOR_GRAY2RGB)
        marks = np.zeros_like(rgb)
        if used_width is not None:
            center = int(self.width/2)
            l = self.slices.shape[0]
            cv2.line(marks, (0,center+used_width), (5,center+used_width), (0,255,0))
            cv2.line(marks, (0,center-used_width), (5,center-used_width), (0,255,0))
            cv2.line(marks, (l-1,center+used_width), (l-6,center+used_width), (0,255,0))
            cv2.line(marks, (l-1,center-used_width), (l-6,center-used_width), (0,255,0))
        return rgb, marks

    def plot_slice(self, w : int, h : int, layer : int) -> np.ndarray:
        """
        Plot a single slice layer.

        Args:
            w (int): Width of the plot.
            h (int): Height of the plot.
            layer (int): The layer index to plot.

        Returns:
            np.ndarray: The RGB plot image.
        """
        xr = np.array(range(self.width))
        values = self.slices[layer]
        rgb = plot_to_numpy(xr, [values], w, h)
        return rgb

    def plot_slices(self, w : int, h : int) -> np.ndarray:
        """
        Plot the mean, max, and min of all slices.

        Args:
            w (int): Width of the plot.
            h (int): Height of the plot.

        Returns:
            np.ndarray: The RGB plot image.
        """
        xr = np.array(range(self.width))
        values = np.mean(self.slices, axis=0)
        top = np.amax(self.slices, axis=0)
        low = np.amin(self.slices, axis=0)
        rgb = plot_to_numpy(xr, [values, top, low], w, h)
        return rgb

class DriftProfile:
    """
    Represents a profile of star track.

    Attributes:
        profile (np.ndarray): The profile data. 1-dimension array
        error (np.ndarray): The error in the profile data. 1-dimension array

    Methods:
        plot_profile(w, h) -> np.ndarray: Plot the profile with error bars.
        plot_profile_with_error(w, h) -> np.ndarray: Plot the profile and its error.
    """
    def __init__(self, profile : np.ndarray, error : np.ndarray | None):
        """
        Initialize a DriftProfile with profile data and optional error.

        Args:
            profile (np.ndarray): The 1D profile data.
            error (np.ndarray | None): The error values for the profile.
        """
        assert len(profile.shape) == 1

        self.profile = profile
        self.length = self.profile.shape[0]
        if error is not None:
            assert error.shape == self.profile.shape
            self.error = error
        else:
            self.error = np.zeros(self.profile.shape)

    def plot_profile(self, w : int, h : int):
        """
        Plot the profile.

        Args:
            w (int): Width of the plot.
            h (int): Height of the plot.

        Returns:
            np.ndarray: The RGB plot image.
        """
        L = self.length
        xr = np.array(list(range(L)))
        rgb = plot_to_numpy(xr, [self.profile], w, h)
        return rgb

    def plot_profile_with_error(self, w : int, h : int):
        """
        Plot the profile with error bounds.

        Args:
            w (int): Width of the plot.
            h (int): Height of the plot.

        Returns:
            np.ndarray: The RGB plot image.
        """
        L = self.length
        xr = np.array(range(L))
        rgb = plot_to_numpy(xr, [self.profile, self.profile + self.error, self.profile - self.error], w, h)
        return rgb

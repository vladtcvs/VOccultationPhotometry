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
        assert right > left, "right must be greater than left"
        assert bottom > top, "bottom must be greater than top"

        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.w = self.right - self.left + 1
        self.h = self.bottom - self.top + 1

    def point_inside_rect(self, x : int, y : int) -> bool:
        return x >= self.left and x <= self.right and y >= self.top and y <= self.bottom

    def specify_position(self, x : int, y : int):
        self.left = x
        self.top = y
        self.right = self.left + self.w - 1
        self.bottom = self.top + self.h - 1

    def specify_size(self, w : int, h : int):
        self.w = w
        self.h = h
        self.right = self.left + self.w - 1
        self.bottom = self.top + self.h - 1

    def detect_overlap(self, other) -> bool:
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
                 half_w : float):
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
        assert len(gray.shape) == 2
        assert margin >= 0

        self.gray = gray                # part of image
        self.margin = margin            # margin
        self.path = path
        self.w = self.gray.shape[1]-2*self.margin
        self.h = self.gray.shape[0]-2*self.margin

    def draw(self, color : tuple, normals_color : tuple, transparency : float) -> np.ndarray:
        rgb = cv2.cvtColor(self.gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        return self.draw_in_place(rgb, 0, 0, color, normals_color, transparency)

    def draw_in_place(self,
                      rgb : np.ndarray,
                      left : int,
                      top : int,
                      path_color : tuple,
                      normals_color : tuple,
                      transparency : float) -> np.ndarray:
        path_color = np.array(path_color)

        # draw points
        if self.path is not None:
            for y, x in self.path.points:
                xx = int(x + left + self.margin)
                yy = int(y + top + self.margin)
                if xx < 0 or yy < 0 or xx >= rgb.shape[1] or yy >= rgb.shape[0]:
                    continue
                rgb[yy, xx] = rgb[yy, xx] * transparency + path_color * (1-transparency)

        # draw normals
        if self.path is not None:
            for index, ((y,x), (ny,nx)) in enumerate(zip(self.path.points, self.path.normals)):
                if index % 10 != 0:
                    continue
                x1 = int(x - nx*self.path.half_w + self.margin)
                y1 = int(y - ny*self.path.half_w + self.margin)
                x2 = int(x + nx*self.path.half_w + self.margin)
                y2 = int(y + ny*self.path.half_w + self.margin)

                cv2.line(rgb, (x1+left,y1+top), (x2+left,y2+top), normals_color, 1)
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
        assert len(slices.shape) == 2

        self.slices = slices
        self.length = self.slices.shape[0] 
        self.width = self.slices.shape[1]
        self.mask = 1-np.isnan(self.slices)
        self.slices[np.where(np.isnan(self.slices))] = 0

    def draw(self, used_width : int) -> Tuple[np.ndarray, np.ndarray]:
        rgb = cv2.cvtColor(self.slices.transpose().astype(np.uint8), cv2.COLOR_GRAY2RGB)
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
        xr = range(self.width)
        values = self.slices[layer]
        rgb = plot_to_numpy(xr, [values], w, h)
        return rgb

    def plot_slices(self, w : int, h : int) -> np.ndarray:
        xr = range(self.width)
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
        assert(len(profile.shape) == 1)

        self.profile = profile
        self.length = self.profile.shape[0]
        if error is not None:
            assert(error.shape == self.profile.shape)
            self.error = error
        else:
            self.error = np.zeros(self.profile.shape)

    def plot_profile(self, w : int, h : int):
        L = self.length
        xr = range(L)
        rgb = plot_to_numpy(xr, [self.profile], w, h)
        return rgb

    def plot_profile_with_error(self, w : int, h : int):
        L = self.length
        xr = range(L)
        rgb = plot_to_numpy(xr, [self.profile, self.profile + self.error, self.profile - self.error], w, h)
        return rgb

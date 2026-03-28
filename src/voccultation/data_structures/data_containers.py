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
    def __init__(self, left, right, top, bottom):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.w = self.right - self.left + 1
        self.h = self.bottom - self.top + 1

    def point_inside_rect(self, x : int, y : int) -> bool:
        return x >= self.left and x <= self.right and y >= self.top and y <= self.bottom

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
    def __init__(self,
                 points : np.ndarray,
                 normals : np.ndarray,
                 half_w : float):
        assert(len(points.shape) == 2)
        assert(points.shape[1] == 2)
        if normals is not None:
            assert(len(normals.shape) == 2)
            assert(points.shape == normals.shape)
        self.points = points            # points [(y, x)]
        self.normals = normals          # normals [(ny, nx)]
        self.half_w = half_w            # 1/2 width of track
        self.length = self.points.shape[0]

class DriftTrack:
    def __init__(self,
                 gray : np.ndarray,
                 margin : int,
                 path : DriftTrackPath):
        self.gray = gray                # part of image
        self.margin = margin            # margin
        self.path = path
        self.w = self.gray.shape[1]-2*self.margin
        self.h = self.gray.shape[0]-2*self.margin

    def draw(self, color : tuple, transparency : float) -> np.ndarray:
        rgb = cv2.cvtColor(self.gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        return self.draw_in_place(rgb, 0, 0, color, transparency)

    def draw_in_place(self, rgb : np.ndarray, left : int, top : int, color : tuple, transparency : float) -> np.ndarray:
        color = np.array(color)

        # draw points
        if self.path is not None:
            for y, x in self.path.points:
                xx = int(x + left + self.margin)
                yy = int(y + top + self.margin)
                if xx < 0 or yy < 0 or xx >= rgb.shape[1] or yy >= rgb.shape[0]:
                    continue
                rgb[yy, xx] = rgb[yy, xx] * transparency + color * (1-transparency)

        # draw normals
        if self.path is not None:
            for index, ((y,x), (ny,nx)) in enumerate(zip(self.path.points, self.path.normals)):
                if index % 10 != 0:
                    continue
                x1 = int(x - nx*self.path.half_w + self.margin)
                y1 = int(y - ny*self.path.half_w + self.margin)
                x2 = int(x + nx*self.path.half_w + self.margin)
                y2 = int(y + ny*self.path.half_w + self.margin)

                cv2.line(rgb, (x1+left,y1+top), (x2+left,y2+top), (0,200,0), 1)
        return rgb

class DriftSlice:
    def __init__(self, slices : np.ndarray):
        self.slices = slices
        self.width = self.slices.shape[1]
        self.mask = 1-np.isnan(self.slices)
        self.slices[np.where(np.isnan(self.slices))] = 0

    def draw(self, used_width : int) -> np.ndarray:
        rgb = cv2.cvtColor(self.slices.transpose().astype(np.uint8), cv2.COLOR_GRAY2RGB)
        if used_width is not None:
            center = int(self.slices.shape[1]/2)
            l = self.slices.shape[0]
            cv2.line(rgb, (0,center+used_width), (5,center+used_width), (0,255,0))
            cv2.line(rgb, (0,center-used_width), (5,center-used_width), (0,255,0))
            cv2.line(rgb, (l-1,center+used_width), (l-6,center+used_width), (0,255,0))
            cv2.line(rgb, (l-1,center-used_width), (l-6,center-used_width), (0,255,0))
        return rgb

    def plot_slice(self, w : int, h : int, layer : int) -> np.ndarray:
        xr = range(self.slices.shape[0])
        values = self.slices[layer]
        rgb = plot_to_numpy(xr, [values], w, h)
        return rgb

    def plot_slices(self, w : int, h : int) -> np.ndarray:
        xr = range(self.slices.shape[0])
        values = np.mean(self.slices, axis=0)
        top = np.amax(self.slices, axis=0)
        low = np.amin(self.slices, axis=0)
        rgb = plot_to_numpy(xr, [values, top, low], w, h)
        return rgb

class DriftProfile:
    def __init__(self, profile : np.ndarray, error : np.ndarray):
        assert(len(profile.shape) == 1)
        self.profile = profile
        self.length = self.profile.shape[0]
        if error is not None:
            assert(error.shape == self.profile.shape)
            self.error = error
        else:
            self.error = np.zeros(self.profile.shape)

    def plot_profile(self, w : int, h : int):
        L = self.profile.shape[0]
        xr = range(L)
        rgb = plot_to_numpy(xr, [self.profile], w, h)
        return rgb

    def plot_profile_with_error(self, w : int, h : int):
        L = self.profile.shape[0]
        xr = range(L)
        rgb = plot_to_numpy(xr, [self.profile, self.profile + self.error, self.profile - self.error], w, h)
        return rgb

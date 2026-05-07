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

from enum import Enum
import numpy as np
from typing import List, Tuple

from voccultation.data_structures.data_containers import DriftTrackPath, DriftTrackRect

class TrackOrientation(Enum):
    TRACK_HORIZONTAL = 0
    TRACK_VERTICAL = 1

def mean_track(tracks : List[DriftTrackRect], image : np.ndarray, margin : int) -> np.ndarray:
    """
    Compute the average track from a list of tracks.

    Parameters:
        tracks (List[DriftTrackRect]): List of tracks to compute the average from.
        image (np.ndarray): Input grayscale image.
        margin (int): Margin around the track.

    Returns:
        np.ndarray: Average track.
    """
    w = tracks[0].w+2*margin
    h = tracks[0].h+2*margin
    sum_track = np.zeros((h,w))
    sum_weight = np.zeros((h,w))
    for track in tracks:
        block, weight = track.extract_track(image, margin)
        sum_track += block
        sum_weight += weight

    sum_track = sum_track / sum_weight
    sum_track[np.where(sum_weight == 0)] = 0
    return sum_track

def _mean_track_to_points(track : np.ndarray,
                          margin : int,
                          orientation : TrackOrientation | None) -> Tuple[np.ndarray, TrackOrientation]:
    """
    Convert a mean track to points - detect position of brightest pixels on each row of image.

    Parameters:
        track (np.ndarray): Mean track image.
        margin (int): Margin around the track.

    Returns:
        Tuple[np.ndarray, bool]: Array of points and flag indicating if the track is transposed.
    """
    w = track.shape[1]
    h = track.shape[0]

    points = []

    if orientation is None:
        if w > h:
            orientation = TrackOrientation.TRACK_HORIZONTAL
        else:
            orientation = TrackOrientation.TRACK_VERTICAL

    if orientation == TrackOrientation.TRACK_HORIZONTAL:
        # horizontal track
        for x in range(margin, w-margin):
            slice = track[:,x]
            maximum = int(slice.argmax())
            points.append((maximum-margin, x-margin))
    else:
        # vertical track
        for y in range(margin, h-margin):
            slice = track[y,:]
            maximum = int(slice.argmax())
            points.append((y-margin,maximum-margin))

    return np.array(points), orientation

def _smooth_track_points(points : np.ndarray, orientation : TrackOrientation, smooth : int) -> np.ndarray:
    """
    Smooth a list of track points.

    Parameters:
        points (np.ndarray): List of track points.
        orientation (TrackOrientation): Flag indicating if the track is more vertical or more horizontal

    Returns:
        np.ndarray: Smoothed list of track points.
    """
    L = points.shape[0]
    if orientation == TrackOrientation.TRACK_VERTICAL:
        index = 1
    else:
        index = 0

    average = np.zeros((L,2))
    for x in range(L):
        s = 0
        num = 0
        for y in range(x-smooth,x+smooth+1):
            if y < 0 or y >= L:
                continue
            s += points[y, index]
            num += 1
        average[x, index] = s / num
        average[x, 1-index] = points[x, 1-index]
    return average

def build_mean_reference_track(gray : np.ndarray,
                               references : List[DriftTrackRect],
                               margin : int,
                               orientation : TrackOrientation | None,
                               smooth : int) -> Tuple[np.ndarray, DriftTrackPath]:
    """
    Build reference track image from a list of tracks.

    Parameters:
        gray (np.ndarray): Input grayscale image.
        references (List[DriftTrackRect]): List of tracks to build the reference track from.
        margin (int): Margin around the track.

    Returns:
        Tuple[np.ndarray, DriftTrackPath]: Reference track image and path.
    """
    track = mean_track(references, gray, margin)
    points, orientation = _mean_track_to_points(track, margin, orientation)
    if smooth != 0:
        points = _smooth_track_points(points, orientation, smooth)
    path = DriftTrackPath(points, None, None)
    return (track, path)

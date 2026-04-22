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
import math

from voccultation.data_structures.data_containers import DriftProfile, DriftSlice, DriftTrackPath

def build_track_normals(points : np.ndarray)-> np.ndarray:
    """
    Builds normals to track at each point.

    Parameters:
        points (np.ndarray): Array of track points

    Returns:
        np.ndarray: Normals to track at each point
    """
    # length of track along main axis
    L = points.shape[0]

    # in each X we have vector of direction of normal
    normals = np.zeros((L, 2))

    # we will use same normal in each point as a first approach
    # it ortogonal to track
    # (ny, nx) = (-tx, ty)

    tx = points[L-1,1] - points[0,1]
    ty = points[L-1,0] - points[0,0]

    nx, ny = ty, -tx
    l = math.sqrt(nx**2+ny**2)
    nx, ny = nx/l, ny/l
    for x in range(L):
        normals[x,0] = ny
        normals[x,1] = nx
    return normals

def interpolate(v1 : float, v2 : float, k):
    """
    Interpolates between two values.

    Parameters:
        v1 (float): First value
        v2 (float): Second value
        k (float): Interpolation coefficient (between 0 and 1)

    Returns:
        float: Interpolated value
    """
    if np.isnan(v1):
        return v2
    if np.isnan(v2):
        return v1
    return v1*(1-k)+v2*k

def _getpixel(track : np.ndarray, y : int, x : int):
    """
    Gets pixel value at specified coordinates.

    Parameters:
        track (np.ndarray): 2D array of pixel values
        y (int): Y-coordinate
        x (int): X-coordinate

    Returns:
        float: Pixel value
    """
    if x < 0 or y < 0:
        return np.nan
    if x >= track.shape[1] or y >= track.shape[0]:
        return np.nan
    return track[y,x]

def getpixel(track : np.ndarray,
             y : float,
             x : float) -> float:
    """
    Gets pixel value at specified coordinates (with bilinear interpolation).

    Parameters:
        track (np.ndarray): 2D array of pixel values
        y (float): Y-coordinate
        x (float): X-coordinate

    Returns:
        float: Pixel value
    """
    y0 = math.floor(y)
    x0 = math.floor(x)
    ky = y - y0
    kx = x - x0
    v00 = _getpixel(track, y = y0, x = x0)
    v01 = _getpixel(track, y = y0, x = x0+1)
    v10 = _getpixel(track, y = y0+1, x = x0)
    v11 = _getpixel(track, y = y0+1, x = x0+1)
    v0 = interpolate(v00, v01, kx)
    v1 = interpolate(v10, v11, kx)
    v = interpolate(v0, v1, ky)
    return v

def _make_slice(track : np.ndarray,
               position : Tuple[float, float],
               direction : Tuple[float, float],
               half_w : int,
               offset : float) -> np.ndarray:
    """
    Creates a slice of the track at specified position and direction.

    Parameters:
        track (np.ndarray): 2D array of pixel values
        position (Tuple[float, float]): Position of the slice
        direction (Tuple[float, float]): Direction of the slice
        half_w (int): Half-width of the slice
        offset (float): Offset from the center

    Returns:
        np.ndarray: Slice of the track
    """
    y,x = position
    ty,tx = direction
    slice = np.zeros((2*half_w+1,))
    for i in range(2*half_w+1):
        s = i - half_w + offset
        py, px = y+ty*s, x+tx*s
        slice[i] = getpixel(track, y=py, x=px)
    return slice

def slice_track(track_image : np.ndarray,
                track_path : DriftTrackPath,
                margin : int,
                offset : float) -> DriftSlice:
    """
    Creates a slice of the track at specified position and direction.

    Parameters:
        track_image (np.ndarray): 2D array of pixel values
        track_path (DriftTrackPath): Track path object
        margin (int): Margin from the center
        offset (float): Offset from the center

    Returns:
        DriftSlice: Slice of the track
    """
    L = track_path.length
    slices = np.zeros((L,2*track_path.half_w+1))
    shift = np.array([margin, margin])
    for i in range(L):
        point = track_path.points[i,:] + shift
        normal = track_path.normals[i,:]
        track_slice = _make_slice(track_image, point, normal, track_path.half_w, offset)
        slices[i,:] = track_slice
    return DriftSlice(slices)

def slice_deconvolution(slices : DriftSlice, psf_sigma : float, snr : float) -> DriftSlice:
    return slices

def slices_to_profile(slices : DriftSlice, used_half_w : int | None) -> DriftProfile:
    """
    Converts a slice to a profile.

    Parameters:
        slices (DriftSlice): Slice of the track
        used_half_w (int): Used width at center

    Returns:
        DriftProfile: Profile of the track
    """
    mask = slices.mask
    slice = slices.slices

    if used_half_w is not None:
        w = 2*used_half_w+1
        pad = (slices.width - w)//2
        mask = mask[:,pad:pad+w]
        slice = slice[:,pad:pad+w]

    weight = np.sum(mask, axis=1) / mask.shape[1]
    value = np.sum(slice, axis=1)
    profile = value / weight
    profile[np.where(np.isnan(profile))] = 0
    return DriftProfile(profile, None)

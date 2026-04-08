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

from typing import List
import numpy as np
import cv2
import imutils
import statistics

from skimage import measure
from voccultation.data_structures.data_containers import DriftTrackRect

def detect_bold_tracks(gray : np.ndarray, 
                       num_tracks : int = 4,
                       smooth_size : int = 11,
                       blur_size : int = 35,
                       threshold_k : float = 1.1) -> List[DriftTrackRect]:
    """
    Detect bold tracks in the input image.

    Parameters:
        gray (np.ndarray): Input grayscale image.
        num_tracks (int, optional): Number of tracks to detect. Defaults to 4.
        smooth_size (int, optional): Size of Gaussian blur for smoothing. Defaults to 11.
        blur_size (int, optional): Size of Gaussian blur for blurring. Defaults to 35.
        threshold_k (float, optional): Threshold value for blob detection. Defaults to 1.1.

    Returns:
        List[DriftTrackRect]: List of detected tracks.
    """
    if blur_size % 2 == 0:
        blur_size += 1
    if smooth_size % 2 == 0:
        smooth_size += 1
    gray = gray / np.amax(gray)
    smooth = cv2.GaussianBlur(gray, (11,11), 0)
    blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
    mask = smooth > blurred * threshold_k + 0.01
    mask = mask.astype('uint8')

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    blob = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    blob = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel)

    labels = measure.label(blob, connectivity=2, background=0)

    numpixels = []

    for label in np.unique(labels):
        if label == 0:
            continue
        label_mask = np.zeros(mask.shape, dtype="uint8")
        label_mask[labels == label] = 1
        num_pixels = cv2.countNonZero(label_mask)
        numpixels.append(num_pixels)

    numpixels = sorted(numpixels, reverse=True)

    if len(numpixels) == 0:
        return None

    tracks = []
    min_pixels = (numpixels[:num_tracks])[-1]
    for label in np.unique(labels):
        if label == 0:
            continue
        label_mask = np.zeros(mask.shape, dtype="uint8")
        label_mask[labels == label] = 1
        num_pixels = cv2.countNonZero(label_mask)
        if num_pixels < min_pixels:
            continue

        contours = cv2.findContours(label_mask,
                                    cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        if len(contours) != 1:
            raise ValueError()
        contour = contours[0]
        left = np.inf
        right = -np.inf
        top = np.inf
        bottom = -np.inf
        for point in contour:
            x, y = point[0]
            left = min(left, x)
            right = max(right, x)
            top = min(top, y)
            bottom = max(bottom, y)
        tracks.append(DriftTrackRect(left, right, top, bottom))

    return tracks

def _clear_overlapped(tracks : List[DriftTrackRect]) -> List[DriftTrackRect]:
    """
    Remove overlapped tracks from the input list.

    Parameters:
        tracks (List[DriftTrackRect]): Input list of tracks.

    Returns:
        List[DriftTrackRect]: Filtered list of non-overlapped tracks.
    """
    not_overlapped = []
    for ind1, track1 in enumerate(tracks):
        for ind2, track2 in enumerate(tracks):
            if ind1 == ind2:
                continue
            if track1.detect_overlap(track2):
                break
        else:
            not_overlapped.append(track1)
    return not_overlapped

def _clear_bad_size(tracks : List[DriftTrackRect], kappa : float) -> List[DriftTrackRect]:
    """
    Remove tracks with sizes outside the specified range from the input list.

    Parameters:
        tracks (List[DriftTrackRect]): Input list of tracks.
        kappa (float): Standard deviation multiplier for size filtering.

    Returns:
        List[DriftTrackRect]: Filtered list of tracks within the specified size range.
    """
    widths = []
    heights = []
    for track in tracks:
        width = int(track.right - track.left)
        height = int(track.bottom - track.top)
        widths.append(width)
        heights.append(height)
    width0 = statistics.mean(widths)
    height0 = statistics.mean(heights)
    stdw = statistics.stdev(widths)
    stdh = statistics.stdev(heights)
    goods = []
    for track in tracks:
        width = track.right - track.left
        height = track.bottom - track.top
        if abs(width - width0) < stdw * kappa and abs(height - height0) < stdh * kappa:
            goods.append(track)
    return goods

def _correlate_tracks(tracks : List[DriftTrackRect]) -> List[DriftTrackRect]:
    """
    Align input tracks to a common size.

    Parameters:
        tracks (List[DriftTrackRect]): Input list of tracks.

    Returns:
        List[DriftTrackRect]: Aligned list of tracks.
    """
    maxw = 0
    maxh = 0
    for track in tracks:
        maxw = max(maxw, track.w)
        maxh = max(maxh, track.h)

    results = []
    for track in tracks:
        # TODO: do correlation
        dx = -int((maxw - track.w)/2)
        dy = -int((maxh - track.h)/2)

        left = track.left + dx
        right = left + maxw - 1
        top = track.top + dy
        bottom = top + maxh - 1
        aligned = DriftTrackRect(left, right, top, bottom)
        results.append(aligned)
    return results

def detect_reference_tracks(gray : np.ndarray,
                            count : int,
                            kappas : List[float]) -> List[DriftTrackRect]:
    """
    Detect reference tracks in the input image.

    Parameters:
        gray (np.ndarray): Input grayscale image.
        count (int): Number of tracks to detect.
        kappas (List[float], optional): List of standard deviation multipliers for size filtering. Defaults to None.

    Returns:
        List[DriftTrackRect]: List of detected reference tracks.
    """
    tracks = detect_bold_tracks(gray, count)
    tracks = _clear_overlapped(tracks)
    if kappas is not None:
        for kappa in kappas:
            tracks = _clear_bad_size(tracks, kappa=kappa)
    tracks = _correlate_tracks(tracks)
    return tracks

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

import numpy as np
import uuid

from voccultation.data_structures.data_containers import DriftProfile, DriftSlice, DriftTrack, DriftTrackPath, DriftTrackRect
from voccultation.methods import drift_profile, drift_slice, tracks_detect
from voccultation.methods.mean_reference_track import build_mean_reference_track

class MeanReferenceTrackContext:
    """Context class for managing and computing mean reference tracks from drift profiles.

    This class provides functionality to handle reference drift tracks, compute a mean
    reference track.
    """
    def __init__(self):
        self.gray : np.ndarray = None
        self.reset()

    def reset(self):
        """Reset the context, clearing any stored data."""
        self.half_w_profile = 5
        self.half_w_cut = 15
        self.update_margin()
        self.clear_reference_tracks()
        self.clear_mean_track()

    def update_margin(self):
        self.margin : int = max(5*self.half_w_profile, self.half_w_cut)

    def clear_reference_tracks(self):
        self.track_rects : dict[str, DriftTrackRect] = {}
        self.labels : dict[str, str] = {}
        self.profiles : dict[str, DriftProfile] = {}

    def clear_mean_track(self):
        """Clear the mean reference track data structures."""
        self.mean_track : DriftTrack = None
        self.mean_slices : DriftSlice = None
        self.mean_profile : DriftProfile = None
        self.mean_image : np.ndarray = None
        self.mean_slices_image : np.ndarray = None
        self.mean_slices_marks : np.ndarray = None
        self.mean_plot : np.ndarray = None

    def update_rect_size(self, width, height):
        if len(self.track_rects) == 0:
            return

        for rect in self.track_rects.values():
            rect.specify_size(width, height)
        self.build_mean_reference_track()

    def specify_track_pos(self, guid, x,  y):
        if guid in self.track_rects:
            self.track_rects[guid].specify_position(x, y)

    def track_position(self, guid : str):
        if guid in self.track_rects:
            x = self.track_rects[guid].left
            y = self.track_rects[guid].top
            return x, y
        return 0, 0

    def set_image(self, gray : np.ndarray):
        self.gray = gray
        self.reset()

    def remove_track(self, guid : str):
        """
        Remove a reference track identified by the given GUID from the context and rebuild mean reference track.

        Arguments:
            guid (str): The identifier of the track to be removed.
        """
        if guid in self.track_rects:
            del self.track_rects[guid]
        if guid in self.profiles:
            del self.profiles[guid]
        if guid in self.labels:
            del self.labels[guid]
        self.build_mean_reference_track()

    def create_new_track(self, guid : str, label : str, default_w : int, default_h : int):
        """
        Create a new track with the specified GUID and label.

        Arguments:
            guid (str): A unique identifier for the new track.
            label (str): A descriptive label for the track.
        """
        if self.gray is None:
            return

        if len(self.track_rects) == 0:
            w = default_w
            h = default_h
        else:
            guid0 = list(self.track_rects.keys())[0]
            w = self.track_rects[guid0].w
            h = self.track_rects[guid0].h
        imgcx = self.gray.shape[1]//2
        imgcy = self.gray.shape[0]//2
        rect = DriftTrackRect(imgcx-w//2, imgcx-w//2+w-1, imgcy-h//2, imgcy-h//2+h-1)
        self.track_rects[guid] = rect
        self.labels[guid] = label

    def assign_label(self, guid : str, label : str):
        self.labels[guid] = label

    def autodetect_tracks(self):
        self.clear_reference_tracks()
        self.clear_mean_track()
        if self.gray is None:
            return
        track_rects_list = tracks_detect.detect_reference_tracks(self.gray, 9, [2, 1.2])
        for rect in track_rects_list:
            new_guid = str(uuid.uuid4())
            self.track_rects[new_guid] = rect

    def set_half_w_cut(self, half_w : int):
        self.half_w_cut = half_w
        if 2*self.half_w_profile > self.half_w_cut:
            self.half_w_profile = int(self.half_w_cut/2)
        self.update_margin()

    def set_half_w_profile(self, half_w : int):
        self.half_w_profile = half_w
        if 2*self.half_w_profile > self.half_w_cut:
            self.half_w_cut = 2*self.half_w_profile
        self.update_margin()

    def build_mean_reference_track(self):
        if len(self.track_rects) == 0:
            self.clear_mean_track()
            return

        # build mean track
        ref_track_area, ref_path = build_mean_reference_track(self.gray,
                                                              list(self.track_rects.values()),
                                                              self.half_w_cut)

        ref_normals = drift_slice.build_track_normals(ref_path.points)
        ref_path = DriftTrackPath(ref_path.points,
                                  ref_normals,
                                  self.half_w_cut)

        self.mean_track = DriftTrack(ref_track_area,
                                     self.half_w_cut,
                                     ref_path)

        # mean track slices
        self.mean_slices = drift_slice.slice_track(ref_track_area,
                                                   self.mean_track.path,
                                                   self.mean_track.margin,
                                                   0)

        # analyze each reference track and find it's profile
        self.profiles.clear()
        for guid in self.track_rects:
            reference_track_rect = self.track_rects[guid]
            track_area, _ = reference_track_rect.extract_track(self.gray,
                                                               self.mean_track.margin)

            # use mean points and normals
            slices = drift_slice.slice_track(track_area,
                                             self.mean_track.path,
                                             self.mean_track.margin,
                                             0)

            self.profiles[guid] = drift_slice.slices_to_profile(slices, self.half_w_profile)

        # find mean reference profile
        self.mean_profile = drift_profile.calculate_reference_profile(list(self.profiles.values()))

    def draw_tracks(self):
        if self.mean_track is not None:
            self.mean_image = self.mean_track.draw((255,0,0), (0,200,0), 0.5)
        else:
            self.mean_image = None

        # mean track slices
        if self.mean_slices is not None:
            ref = self.mean_slices.draw(self.half_w_profile)
            self.mean_slices_image = ref[0]
            self.mean_slices_marks = ref[1]
        else:
            self.mean_slices_image = None
            self.mean_slices_marks = None

        # build reference profile plot
        if self.mean_profile is not None:
            self.mean_plot = self.mean_profile.plot_profile(640, 480)
        else:
            self.mean_plot = None

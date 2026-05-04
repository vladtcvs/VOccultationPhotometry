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
from voccultation.methods import drift_profile, drift_slice, mean_reference_track, tracks_detect

class MeanReferenceTrackContext:
    def __init__(self):
        self.gray : np.ndarray = None
        self.reset()

    def reset(self):
        self.half_w_profile = 5
        self.half_w_cut = 15
        self.margin : int = max(5*self.half_w_profile, self.half_w_cut)
        self.track_rects : dict[str, DriftTrackRect] = {}
        self.labels : dict[str, str] = {}
        self.mean_track : DriftTrack = None
        self.mean_slices : DriftSlice = None
        self.profiles : dict[str, DriftProfile] = {}
        self.mean_profile : DriftProfile = None
        self.mean_image : np.ndarray = None
        self.mean_slices_image : np.ndarray = None
        self.mean_slices_marks : np.ndarray = None
        self.mean_plot : np.ndarray = None

    def set_image(self, gray : np.ndarray):
        self.gray = gray
        self.reset()

    def remove_track(self, guid : str):
        del self.track_rects[guid]
        del self.profiles[guid]
        if guid in self.labels:
            del self.labels[guid]

    def add_new_track(self, guid : str, label : str):
        if len(self.track_rects) == 0:
            w = 50
            h = 50
        else:
            guid0 = list(self.track_rects.keys())[0]
            w = self.track_rects[guid0].w
            h = self.track_rects[guid0].h
        imgcx = self.gray.shape[1]//2
        imgcy = self.gray.shape[0]//2
        rect = DriftTrackRect(imgcx-w//2, imgcx-w//2+w-1, imgcy-h//2, imgcy-h//2+h-1)
        self.track_rects[guid] = rect
        self.labels[guid] = label

    def reset_labels(self):
        self.labels.clear()

    def add_label(self, guid : str, label : str):
        self.labels[guid] = label

    def autodetect_tracks(self):
        self.reset()
        if self.gray is not None:
            self.track_rects.clear()
            track_rects_list = tracks_detect.detect_reference_tracks(self.gray, 9, [2, 1.2])
            for rect in track_rects_list:
                guid = str(uuid.uuid4())
                self.track_rects[guid] = rect

    def set_half_w_cut(self, half_w : int):
        self.half_w_cut = half_w
        if 2*self.half_w_profile > self.half_w_cut:
            self.half_w_profile = int(self.half_w_cut/2)
        self.margin = max(5*self.half_w_profile, self.half_w_cut)

    def set_half_w_profile(self, half_w : int):
        self.half_w_profile = half_w
        if 2*self.half_w_profile > self.half_w_cut:
            self.half_w_cut = 2*self.half_w_profile
        self.margin = max(5*self.half_w_profile, self.half_w_cut)

    def build_mean_reference_track(self):
        if len(self.track_rects) == 0:
            self.reset()
            return

        # build mean track
        ref_track_area, ref_path = mean_reference_track.build_mean_reference_track(self.gray,
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

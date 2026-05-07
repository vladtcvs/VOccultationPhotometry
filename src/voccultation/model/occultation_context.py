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

from voccultation.data_structures.data_containers import DriftProfile, DriftSlice, DriftTrack, DriftTrackPath, DriftTrackRect
from voccultation.methods import drift_profile, drift_slice


class OccultationTrackContext:
    def __init__(self):
        self.gray : np.ndarray = None
        self.reset()

    def set_image(self, gray : np.ndarray):
        self.gray = gray
        self.reset()

    def reset(self):
        if self.gray is None:
            self.track_pos = (0, 0)
        else:
            self.track_pos = (self.gray.shape[1]//2, self.gray.shape[0]//2)

        self.half_w_profile : int = 5
        self.half_w_cut : int = 15
        self.update_margin()
        self.clear_reference_track()

    def update_margin(self):
        self.margin : int = max(5*self.half_w_profile, self.half_w_cut)

    def clear_reference_track(self):
        self.reference_track : DriftTrack = None
        self.track_rect : DriftTrackRect = None
        self.track : DriftTrack = None
        self.sky_tracks : List[DriftTrack] = []
        self.slices : DriftSlice = None
        self.side_slices : List[DriftSlice] = []
        self.profile : DriftProfile = None
        self.image : np.ndarray = None
        self.slices_image : np.ndarray = None
        self.slices_marks : np.ndarray = None
        self.plot : np.ndarray = None

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

    def track_position(self):
        x = self.track_pos[1]
        y = self.track_pos[0]
        return x, y

    def specify_track_pos(self, x0 : int, y0 : int):
        """
        Specify occultation track position in the drift context.

        Parameters:
            x0 (int): X-coordinate of the position.
            y0 (int): Y-coordinate of the position.
        """
        self.track_pos = (y0, x0)
        if self.track_rect is not None:
            self.track_rect.specify_position(x0, y0)

    def specify_reference_track(self, reference_track : DriftTrack):
        if reference_track is None:
            self.clear_reference_track()
            return
        (y0, x0) = self.track_pos
        w = reference_track.w
        h = reference_track.h
        self.reference_track = reference_track
        self.track_rect = DriftTrackRect(x0, x0 + w, y0, y0 + h)
        occultation_track_area, _ = self.track_rect.extract_track(self.gray, self.margin)
        occ_path = DriftTrackPath(self.reference_track.path.points,
                                  self.reference_track.path.normals,
                                  self.half_w_cut)

        self.track = DriftTrack(occultation_track_area,
                                self.margin,
                                occ_path)

    def build_occultation_profile(self, remove_sky : bool):
        # profile of track
        if self.track is None:
            return
        self.side_slices.clear()
        self.slices = drift_slice.slice_track(self.track.gray,
                                              self.track.path,
                                              self.track.margin,
                                              0)

        # profiles parallel to track
        for i in (-4,-2,2,4):
            offsetes_slice = drift_slice.slice_track(self.track.gray,
                                                     self.track.path,
                                                     self.track.margin,
                                                     i*self.half_w_profile)
            self.side_slices.append(offsetes_slice)

        # build profile
        self.profile = drift_slice.slices_to_profile(self.slices,
                                                                 self.half_w_profile)

        if remove_sky:
            occultation_side_profiles = []
            for slice in self.side_slices:
                profile = drift_slice.slices_to_profile(slice, self.half_w_profile)
                occultation_side_profiles.append(profile)

            sky_profile = drift_profile.calculate_sky_profile(occultation_side_profiles)
            self.profile.profile = self.profile.profile - sky_profile.profile
        else:
            pass

    def draw_track(self):
        if self.track is not None:
            self.image = self.track.draw((0,200,0), (0,200,0), 0.5)
        else:
            self.image = None

        # occultation slices
        if self.slices is not None:
            ref = self.slices.draw(self.half_w_profile)
            self.slices_image = ref[0]
            self.slices_marks = ref[1]
        else:
            self.slices_image = None
            self.slices_marks = None

        # build occultation profile plot
        if self.profile is not None:
            self.plot = self.profile.plot_profile(640, 480)
        else:
            self.plot = None

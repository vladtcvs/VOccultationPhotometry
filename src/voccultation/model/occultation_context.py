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

"""Occultation track context and profile building logic.

Manages the state machine for loading images, specifying reference tracks,
extracting slices, computing sky-subtracted profiles, and generating visualizations.
"""

import enum
from typing import List, Tuple
import numpy as np

from voccultation.data_structures.data_containers import DriftProfile, DriftSlice, DriftTrack
from voccultation.data_structures.data_containers import DriftTrackPath, DriftTrackRect
from voccultation.methods import drift_profile, drift_slice


# State Transition Diagrams
#
# ImageState:
#   INIT  -->  IMAGE_LOADED   (via set_image())
#     ^               |
#     |               v
#     +---<---  (via clear_image() / reset())
#
# ProfileState:
#   INIT  -->  REFERENCE_SPECIFIED   (via specify_reference_track())
#     |                 |
#     |                 v
#     |          PROFILE_BUILT
#     |                 |
#     +---<-------------+   (via clear_reference_track() / reset())
#

class OccultationTrackContext:
    """
    Context class for managing occultation track analysis.

    Handles image loading, reference track specification, and profile building
    for occultation measurements.
    """
    class ImageState(enum.Enum):
        """State of the loaded image."""
        INIT = 0
        IMAGE_LOADED = 1

    class ProfileState(enum.Enum):
        """State of the occultation profile."""
        INIT = 0
        REFERENCE_SPECIFIED = 1
        PROFILE_BUILT = 2

    def __init__(self):
        """
        Initialize the OccultationTrackContext.
        """
        self.image_state = self.ImageState.INIT
        self.profile_state = self.ProfileState.INIT
        self.gray : np.ndarray | None = None
        self.reset()

    def clear_image(self):
        """
        Clear the loaded image and reset the context.
        """
        self.image_state = self.ImageState.INIT
        self.gray = None
        self.reset()

    def set_image(self, gray : np.ndarray):
        """
        Set the grayscale image for occultation analysis.

        Args:
            gray (np.ndarray): The input grayscale image.
        """
        assert gray is not None
        self.image_state = self.ImageState.IMAGE_LOADED
        self.gray = gray
        self.reset()

    def reset(self):
        """
        Reset all track and profile data to initial state.
        """
        self.half_w_profile : int = 5
        self.half_w_cut : int = 15
        self.update_margin()
        self.clear_reference_track()

    def update_margin(self):
        """
        Update the margin based on current half-width settings.
        """
        self.margin : int = max(5*self.half_w_profile, self.half_w_cut)

    def clear_reference_track(self):
        """
        Clear all reference track and derived data.
        """
        self.reference_track : DriftTrack | None = None
        self.track_rect : DriftTrackRect | None = None
        self.track : DriftTrack | None = None
        self.sky_tracks : List[DriftTrack] = []
        self.slices : DriftSlice | None = None
        self.side_slices_list : List[DriftSlice] = []
        self.profile : DriftProfile | None = None
        self.image : np.ndarray | None = None
        self.slices_image : np.ndarray | None = None
        self.slices_marks : np.ndarray | None = None
        self.plot : np.ndarray | None = None
        self.profile_state = self.ProfileState.INIT

    def set_half_w_cut(self, half_w : int):
        """
        Set the half-width used for cutting the track.

        Args:
            half_w (int): The new half-width value.
        """
        self.half_w_cut = half_w
        if 2*self.half_w_profile > self.half_w_cut:
            self.half_w_profile = int(self.half_w_cut/2)
        self.update_margin()

    def set_half_w_profile(self, half_w : int):
        """
        Set the half-width used for profile extraction.

        Args:
            half_w (int): The new half-width value.
        """
        self.half_w_profile = half_w
        if 2*self.half_w_profile > self.half_w_cut:
            self.half_w_cut = 2*self.half_w_profile
        self.update_margin()

    def track_position(self) -> Tuple[int,int]:
        """
        Get the current track position.

        Returns:
            Tuple[int, int]: The (x, y) coordinates of the track.
        """
        if self.profile_state is self.ProfileState.INIT:
            return 0, 0
        assert self.track_rect is not None
        x = self.track_rect.left
        y = self.track_rect.top
        return x, y

    def specify_track_pos(self, x0 : int, y0 : int):
        """
        Specify occultation track position in the drift context.

        Parameters:
            x0 (int): X-coordinate of the position.
            y0 (int): Y-coordinate of the position.
        """
        if self.profile_state is self.ProfileState.INIT:
            return
        assert self.track_rect is not None
        self.track_rect.specify_position(x0, y0)

    def specify_reference_track(self, reference_track : DriftTrack):
        """
        Specify a reference track for occultation analysis.

        Args:
            reference_track (DriftTrack): The reference track to use.
        """
        assert reference_track is not None
        if self.image_state is not self.ImageState.IMAGE_LOADED:
            return
        assert self.gray is not None
        if self.profile_state is self.ProfileState.INIT:
            x0, y0 = (self.gray.shape[1]//2, self.gray.shape[0]//2)
        else:
            x0, y0 = self.track_position()

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
        self.profile_state = self.ProfileState.REFERENCE_SPECIFIED

    def build_occultation_profile(self, remove_sky : bool):
        """
        Build the occultation profile from the current track.

        Args:
            remove_sky (bool): Whether to subtract sky background.
        """
        # profile of track
        if self.image_state is self.ImageState.INIT:
            return
        if self.profile_state is self.ProfileState.INIT:
            return
        assert self.track is not None
        self.side_slices_list.clear()
        self.slices = drift_slice.slice_track(self.track.gray,
                                              self.track.path,
                                              self.track.margin,
                                              0)

        # profiles parallel to track
        for i in (-4,-2,2,4):
            offseted_slices = drift_slice.slice_track(self.track.gray,
                                                     self.track.path,
                                                     self.track.margin,
                                                     i*self.half_w_profile)
            self.side_slices_list.append(offseted_slices)

        # build profile
        self.profile = drift_slice.slices_to_profile(self.slices,
                                                     self.half_w_profile)

        if remove_sky:
            occultation_side_profiles = []
            for side_slices in self.side_slices_list:
                profile = drift_slice.slices_to_profile(side_slices, self.half_w_profile)
                occultation_side_profiles.append(profile)

            sky_profile = drift_profile.calculate_sky_profile(occultation_side_profiles)
            self.profile.profile = self.profile.profile - sky_profile.profile
        else:
            pass
        self.profile_state = self.ProfileState.PROFILE_BUILT

    def draw_track(self):
        """
        Generate visualization images for the track, slices, and profile.
        """
        if self.profile_state is not self.ProfileState.INIT:
            assert self.track is not None
            self.image = self.track.draw((0,200,0), (0,200,0), 0.5, 1)
        else:
            self.image = None

        # occultation slices
        if self.profile_state is self.ProfileState.PROFILE_BUILT:
            assert self.slices is not None
            ref = self.slices.draw(self.half_w_profile)
            self.slices_image = ref[0]
            self.slices_marks = ref[1]
        else:
            self.slices_image = None
            self.slices_marks = None

        # build occultation profile plot
        if self.profile_state is self.ProfileState.PROFILE_BUILT:
            assert self.profile is not None
            self.plot = self.profile.plot_profile(640, 480)
        else:
            self.plot = None

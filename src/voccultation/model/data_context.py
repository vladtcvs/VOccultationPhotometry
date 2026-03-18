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

import voccultation.model.drift_profile as drift_profile
import voccultation.model.drift_slice as drift_slice
import voccultation.model.drift_detect as drift_detect

from voccultation.model.data_containers import DriftTrackRect, DriftProfile, DriftTrack, DriftSlice

import abc
from typing import List, Tuple

import cv2
import numpy as np

class IObserver:
    @abc.abstractmethod
    def notify(self):
        pass

class DriftContext:
    def __init__(self):
        self.observers : List[IObserver] = []

        # original frame
        self.gray : np.ndarray = None

        # reference track half width
        self.reference_half_w = 5

        # occultation track half width
        self.occultation_half_w = 5

        # occultation track margin
        self.occultation_margin = 10

        # smoothing error of profiles
        self.smooth_err = 21

        # restore true reference profile
        self.build_true_occultation_profile : bool = True

        self.occultation_track_pos = (0,0)

        # ---------- detected track rectangles ---------

        self.reference_track_rects : List[DriftTrackRect] = []
        self.occultation_track_rect : DriftTrackRect = None

        # ---------- detected tracks -------------------

        self.reference_tracks : List[DriftTrack] = []
        self.occultation_track : DriftTrack = None
        self.sky_tracks : List[DriftTrack] = []

        # ---------- average reference track -----------

        self.mean_reference_track : DriftTrack = None
        self.mean_reference_slices : DriftSlice = None

        # ---------- occultation slices ----------------
        self.occultation_slices : DriftSlice = None

        # ---------- profiles --------------------------
        self.reference_profiles : List[DriftProfile] = []
        self.mean_reference_profile : DriftProfile = None
        self.occultation_profile : DriftProfile = None

        # ----------- track images ---------------------

        self.mean_reference_image : np.ndarray = None
        self.occultation_image : np.ndarray = None

        # ---------- plots -----------------------------

        self.mean_reference_plot : np.ndarray = None
        self.occultation_plot : np.ndarray = None

    def add_observer(self, observer : IObserver):
        self.observers.append(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.notify()

    def set_image(self, gray : np.ndarray):
        self.gray = gray
        self.rgb = cv2.cvtColor(self.gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        self.notify_observers()

    def set_reference_half_w(self, half_w : int):
        self.reference_half_w = half_w
        self.notify_observers()

    def set_occultation_half_w(self, half_w : int):
        self.occultation_half_w = half_w
        self.notify_observers()

    def _draw_tracks(self):
        self.rgb = cv2.cvtColor(self.gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)

        # mean track draw
        if self.mean_reference_track is not None:
            self.mean_reference_image = self.mean_reference_track.draw((255,0,0), 0.5)
        else:
            self.mean_reference_image = None

        # build reference profile plot
        if self.mean_reference_profile is not None:
            self.mean_reference_plot = self.mean_reference_profile.plot_profile(640, 480)
        else:
            self.mean_reference_plot = None

        # occultation track draw
        if self.occultation_track is not None:
            self.occultation_image = self.occultation_track.draw((0,200,0),0.5)
        else:
            self.occultation_image = None

        # build occultation profile plot
        if self.occultation_profile is not None:
            self.occultation_plot = self.occultation_profile.plot_profile(640, 480)
        else:
            self.occultation_plot = None

        # draw reference track line on each of reference tracks on original image
        for reference_track_rect in self.reference_track_rects:
                # draw track
                if self.mean_reference_track is not None:
                    reference_track_area, _ = reference_track_rect.extract_track(self.gray, 0)
                    reference_track = DriftTrack(reference_track_area,
                                                 margin=0,
                                                 points=self.mean_reference_track.points,
                                                 normals=self.mean_reference_track.normals,
                                                 half_w=self.mean_reference_track.half_w)
                    reference_track.draw_in_place(self.rgb, reference_track_rect.left, reference_track_rect.top, (255,0,0), 0.5)

                # draw bounding rectangle
                cv2.rectangle(self.rgb, (reference_track_rect.left, reference_track_rect.top),
                                        (reference_track_rect.right, reference_track_rect.bottom),
                                        color=(255,0,0), thickness=1)

        # draw occultation track
        if self.occultation_track_rect is not None:
            if self.occultation_track is not None:
                occultation_track_area, _ = self.occultation_track_rect.extract_track(self.gray, 0)
                occultation_track = DriftTrack(occultation_track_area,
                                               margin=0,
                                               points=self.occultation_track.points,
                                               normals=self.occultation_track.normals,
                                               half_w=self.occultation_track.half_w
                                               )
                occultation_track.draw_in_place(self.rgb, self.occultation_track_rect.left, self.occultation_track_rect.top, (0,200,0), 0.5)

            # draw bounding rectangles
            cv2.rectangle(self.rgb, (self.occultation_track_rect.left,
                                     self.occultation_track_rect.top),
                                    (self.occultation_track_rect.right,
                                     self.occultation_track_rect.bottom),
                                    color=(0,200,0), thickness=1)

            cv2.rectangle(self.rgb, (self.occultation_track_rect.left-self.occultation_margin,
                                     self.occultation_track_rect.top-self.occultation_margin),
                                    (self.occultation_track_rect.right+self.occultation_margin,
                                     self.occultation_track_rect.bottom+self.occultation_margin),
                                    color=(0,200,0), thickness=1)

    def detect_tracks(self):
        self.reference_track_rects = drift_detect.detect_reference_tracks(self.gray, 9, [2, 1.2])
        self.mean_reference_track = None
        self.mean_reference_profile = None
        self.mean_reference_image = None
        self.mean_reference_plot = None
        self.mean_reference_slices = None

        # draw track bounding rectangles
        self._draw_tracks()
        self.notify_observers()

    def build_mean_reference_track(self):
        if len(self.reference_track_rects) == 0:
            self.mean_reference_track = None
            self.mean_reference_profile = None
            self.mean_reference_image = None
            self.mean_reference_plot = None
            self.mean_reference_slices = None
            self._draw_tracks()
            self.notify_observers()
            return

        # build mean track
        ref_track_area, ref_points, _ = drift_detect.build_mean_reference_track(self.gray, self.reference_track_rects)
        ref_normals = drift_slice.build_track_normals(ref_points)
        self.mean_reference_track = DriftTrack(ref_track_area, 0, ref_points, ref_normals, self.reference_half_w)

        # mean track slices
        slices = drift_slice.slice_track(ref_track_area,
                                         self.mean_reference_track.points,
                                         self.mean_reference_track.normals,
                                         self.mean_reference_track.half_w,
                                         0, 0)
        self.mean_reference_slices = DriftSlice(slices)

        # analyze each reference track and find it's profile
        ref_profiles : List[np.ndarray] = []
        for reference_track_rect in self.reference_track_rects:
            track_area, _ = reference_track_rect.extract_track(self.gray, 0)
            # use mean points and normals
            slices = drift_slice.slice_track(track_area,
                                             self.mean_reference_track.points,
                                             self.mean_reference_track.normals,
                                             self.mean_reference_track.half_w,
                                             0, 0)
            reference_track_slices = DriftSlice(slices)

            profile = drift_slice.slices_to_profile(reference_track_slices.slices)
            ref_profiles.append(profile)

        self.reference_profiles = [DriftProfile(profile, np.zeros(profile.shape)) for profile in ref_profiles]

        # find mean reference profile
        ref_profile, ref_stdev = drift_profile.calculate_reference_profile(ref_profiles)
        self.mean_reference_profile = DriftProfile(ref_profile, ref_stdev)

        # draw tracks
        self._draw_tracks()
        self.notify_observers()

    def build_occultation_track(self, x0 : int, y0 : int):
        if self.mean_reference_track is None:
            self.occultation_track_rect = None
            self.occultation_track = None
            self.occultation_slices = None
            self.occultation_profile = None
            return

        w = self.mean_reference_track.gray.shape[1]
        h = self.mean_reference_track.gray.shape[0]
        self.occultation_track_rect = DriftTrackRect(x0, x0 + w, y0, y0 + h)

        occultation_track_area, _ = self.occultation_track_rect.extract_track(self.gray, self.occultation_margin)
        self.occultation_track = DriftTrack(occultation_track_area,
                                            self.occultation_margin,
                                            self.mean_reference_track.points,
                                            self.mean_reference_track.normals,
                                            self.occultation_half_w)

        # profile of track
        slices = drift_slice.slice_track(self.occultation_track.gray,
                                         self.occultation_track.points,
                                         self.occultation_track.normals,
                                         self.occultation_track.half_w,
                                         self.occultation_track.margin,
                                         0)

        self.occultation_slices = DriftSlice(slices)

        occultation_profile_raw = drift_slice.slices_to_profile(slices)

        # profiles parallel to track
        side_profiles = []
        for i in (-4,-2,2,4):
            occultation_slices_offset = drift_slice.slice_track(self.occultation_track.gray,
                                                                self.occultation_track.points,
                                                                self.occultation_track.normals,
                                                                self.occultation_track.half_w,
                                                                self.occultation_track.margin,
                                                                i*self.occultation_track.half_w)
            occ_profile_offset = drift_slice.slices_to_profile(occultation_slices_offset)
            side_profiles.append(occ_profile_offset)

        # Profile without sky glow
        if self.build_true_occultation_profile:
            reference_profiles = [profile.profile for profile in self.reference_profiles]
            occ_profile, occ_profile_stdev, stats = drift_profile.calculate_true_drift_profile(occultation_profile_raw,
                                                                                               side_profiles,
                                                                                               reference_profiles)
            self.occultation_profile = DriftProfile(occ_profile, occ_profile_stdev)
            for key in stats:
                print(f"{key} : {stats[key]}")
        else:
            _, sky_stdev = drift_profile.calculate_sky_profile(side_profiles)
            self.occultation_profile = DriftProfile(occultation_profile_raw, sky_stdev)

        self._draw_tracks()
        self.notify_observers()

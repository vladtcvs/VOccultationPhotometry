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

from voccultation.data_structures.data_containers import DriftTrackRect, DriftProfile, DriftTrack, DriftSlice, DriftTrackPath

import voccultation.methods.drift_profile as drift_profile
import voccultation.methods.drift_slice as drift_slice
import voccultation.methods.tracks_detect as tracks_detect
import voccultation.methods.mean_reference_track as mean_reference_track

import abc
from typing import List

import cv2
import numpy as np

class IObserver:
    @abc.abstractmethod
    def notify(self):
        pass

class DriftContext:
    def __init__(self):
        """
        Initialize the drift context with empty data.
        """
        self.observers : List[IObserver] = []

        # original frame
        self.gray : np.ndarray = None

        # reference track half width
        self.reference_half_w_cut = 15
        self.reference_half_w_profile = 5

        # occultation track half width
        self.occultation_half_w = 5

        # occultation track margin
        self.occultation_margin = 10

        # smoothing error of profiles
        self.smooth_err = 21

        # restore true reference profile
        self.remove_sky : bool = True
        self.deconvolution : bool = True
        self.compensate_speed : bool = True

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
        self.psf_sigma : float = 0
        self.psf_snr : float = 10.0

        # ---------- occultation slices ----------------
        self.occultation_slices : DriftSlice = None
        self.occultation_side_slices : List[DriftSlice] = []

        # ---------- profiles --------------------------
        self.reference_profiles : List[DriftProfile] = []
        self.mean_reference_profile : DriftProfile = None
        self.occultation_profile : DriftProfile = None

        # ----------- track images ---------------------

        self.mean_reference_image : np.ndarray = None
        self.occultation_image : np.ndarray = None

        # ----------- slice images ---------------------

        self.mean_reference_slices_image : np.ndarray = None
        self.occultation_slices_image : np.ndarray = None

        # ---------- plots -----------------------------

        self.mean_reference_plot : np.ndarray = None
        self.occultation_plot : np.ndarray = None

    def add_observer(self, observer : IObserver):
        """
        Add an observer to the drift context.

        Parameters:
            observer (IObserver): Observer to add.
        """
        self.observers.append(observer)

    def notify_observers(self):
        """
        Notify all observers in the drift context.
        """
        for observer in self.observers:
            observer.notify()

    def set_image(self, gray : np.ndarray):
        """
        Set the image for the drift context.

        Parameters:
            gray (np.ndarray): Grayscale image to set.
        """
        self.gray = gray
        self.rgb = cv2.cvtColor(self.gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        self.notify_observers()

    def set_reference_half_w_cut(self, half_w : int):
        """
        Set the reference track half width value for track slices extraction.

        Parameters:
            half_w (int): New half width cut value.
        """
        self.reference_half_w_cut = half_w
        if 2*self.reference_half_w_profile > self.reference_half_w_cut:
            self.reference_half_w_profile = int(self.reference_half_w_cut/2)
        self.notify_observers()
    
    def set_reference_half_w_profile(self, half_w : int):
        """
        Set the reference track half width value for track profile calculation.

        Parameters:
            half_w (int): New half width profile value.
        """
        self.reference_half_w_profile = half_w
        if 2*self.reference_half_w_profile > self.reference_half_w_cut:
            self.reference_half_w_cut = 2*self.reference_half_w_profile
        self.notify_observers()

    def set_occultation_half_w(self, half_w : int):
        """
        Set the occultation track half width value.

        Parameters:
            half_w (int): New half width value.
        """
        self.occultation_half_w = half_w
        self.notify_observers()

    def set_psf_sigma(self, sigma : float):
        """
        Set star PSF sigma

        Parameters:
            sigma (float): PSF sigma
        """
        self.psf_sigma = sigma
        self.notify_observers()

    def set_psf_snr(self, snr : float):
        """
        Set star PSF SNR

        Parameters:
            snr (float): PSF SNR
        """
        self.psf_snr = snr
        self.notify_observers()

    def display_tracks(self):
        """
        Display tracks in the drift context.
        """
        if self.gray is None:
            self.rgb = None
            return

        self.rgb = cv2.cvtColor(self.gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        # draw reference track line on each of reference tracks on original image
        for reference_track_rect in self.reference_track_rects:
                # draw track
                if self.mean_reference_track is not None:
                    reference_track_area, _ = reference_track_rect.extract_track(self.gray, 0)
                    reference_track = DriftTrack(reference_track_area,
                                                 margin=0,
                                                 path=self.mean_reference_track.path)
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
                                               path=self.mean_reference_track.path)

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
        self.notify_observers()

    def _draw_tracks(self):
        # mean track draw
        if self.mean_reference_track is not None:
            self.mean_reference_image = self.mean_reference_track.draw((255,0,0), 0.5)
        else:
            self.mean_reference_image = None

        # mean track slices
        if self.mean_reference_slices is not None:
            self.mean_reference_slices_image = self.mean_reference_slices.draw(self.reference_half_w_profile)
        else:
            self.mean_reference_slices_image = None

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

        # occultation slices
        if self.occultation_slices is not None:
            self.occultation_slices_image = self.occultation_slices.draw(None)
        else:
            self.occultation_slices_image = None

        # build occultation profile plot
        if self.occultation_profile is not None:
            self.occultation_plot = self.occultation_profile.plot_profile(640, 480)
        else:
            self.occultation_plot = None

        self.display_tracks()

    def detect_tracks(self):
        """
        Detect tracks in the drift context.
        """
        self.mean_reference_track = None
        self.mean_reference_profile = None
        self.mean_reference_image = None
        self.mean_reference_plot = None
        self.mean_reference_slices = None
        if self.gray is None:
            self.reference_track_rects = []
        else:
            self.reference_track_rects = tracks_detect.detect_reference_tracks(self.gray, 9, [2, 1.2])

        # draw track bounding rectangles
        self._draw_tracks()
        self.notify_observers()

    def estimate_psf_sigma(self):
        if self.mean_reference_slices is not None:
            self.psf_sigma = drift_slice.estimate_psf(self.mean_reference_slices)
        else:
            self.psf_sigma = 0

    def estimate_psf_snr(self):
        if self.occultation_slices is not None:
            self.psf_snr = 100
        else:
            self.psf_snr = 100.0

    def build_mean_reference_track(self):
        """
        Build mean reference track in the drift context.
        """
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
        ref_track_area, ref_path = mean_reference_track.build_mean_reference_track(self.gray,
                                                                                   self.reference_track_rects,
                                                                                   self.reference_half_w_cut)

        ref_normals = drift_slice.build_track_normals(ref_path.points)
        ref_path = DriftTrackPath(ref_path.points,
                                  ref_normals,
                                  self.reference_half_w_cut)
        self.mean_reference_track = DriftTrack(ref_track_area,
                                               self.reference_half_w_cut,
                                               ref_path)

        # mean track slices
        self.mean_reference_slices = drift_slice.slice_track(ref_track_area,
                                         self.mean_reference_track.path,
                                         self.mean_reference_track.margin,
                                         0)

        # analyze each reference track and find it's profile
        self.reference_profiles.clear()
        for reference_track_rect in self.reference_track_rects:
            track_area, _ = reference_track_rect.extract_track(self.gray, self.mean_reference_track.margin)
            # use mean points and normals
            slices = drift_slice.slice_track(track_area,
                                             self.mean_reference_track.path,
                                             self.mean_reference_track.margin,
                                             0)

            self.reference_profiles.append(drift_slice.slices_to_profile(slices))

        # find mean reference profile
        self.mean_reference_profile = drift_profile.calculate_reference_profile(self.reference_profiles)

        # draw tracks
        self._draw_tracks()
        self.notify_observers()

    def specify_occultation_track(self, x0 : int, y0 : int):
        """
        Specify occultation track position in the drift context.

        Parameters:
            x0 (int): X-coordinate of the position.
            y0 (int): Y-coordinate of the position.
        """
        if self.mean_reference_track is None:
            self.occultation_track_rect = None
            self.occultation_track = None
            self.occultation_slices = None
            self.occultation_profile = None
            return
        self.occultation_track_pos = (y0, x0)
        w = self.mean_reference_track.w
        h = self.mean_reference_track.h
        self.occultation_track_rect = DriftTrackRect(x0, x0 + w, y0, y0 + h)

    def build_occultation_track(self):
        """
        Build occultation track in the drift context.
        """
        if self.mean_reference_track is None:
            self.occultation_track_rect = None
            self.occultation_track = None
            self.occultation_slices = None
            self.occultation_profile = None
            return

        occultation_track_area, _ = self.occultation_track_rect.extract_track(self.gray, self.occultation_margin)
        occ_path = DriftTrackPath(self.mean_reference_track.path.points, self.mean_reference_track.path.normals, self.occultation_half_w)
        self.occultation_track = DriftTrack(occultation_track_area,
                                            self.occultation_margin,
                                            occ_path)

        # profile of track
        self.occultation_slices = drift_slice.slice_track(self.occultation_track.gray,
                                         self.occultation_track.path,
                                         self.occultation_track.margin,
                                         0)

        # profiles parallel to track
        self.occultation_side_slices = []
        for i in (-4,-2,2,4):
            offsetes_slice = drift_slice.slice_track(self.occultation_track.gray,
                                                     self.occultation_track.path,
                                                     self.occultation_track.margin,
                                                     i*self.occultation_track.path.half_w)
            self.occultation_side_slices.append(offsetes_slice)

        # Restore true profile

        params = {
            "remove_sky" : self.remove_sky,
            "deconvolution" : self.deconvolution,
            "compensate_speed" : self.compensate_speed,
            "psf" : {
                "sigma" : self.psf_sigma,
                "snr" : self.psf_snr,
            }
        }

        self.occultation_profile, stats = drift_profile.calculate_true_drift_profile(self.occultation_slices,
                                                                                     self.occultation_side_slices,
                                                                                     self.mean_reference_profile,
                                                                                     params)
        for key in stats:
            print(f"{key} : {stats[key]}")

        self._draw_tracks()
        self.notify_observers()

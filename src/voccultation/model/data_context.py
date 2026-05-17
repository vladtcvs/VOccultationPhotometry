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

import abc
import enum
from typing import List

import cv2
import numpy as np

from voccultation.data_structures.data_containers import DriftTrack
from voccultation.model.occultation_context import OccultationTrackContext
from voccultation.model.reference_context import MeanReferenceTrackContext

class IObserver:
    @abc.abstractmethod
    def notify(self):
        pass

class DriftContext:

    class ImageState(enum.Enum):
        INIT = 0
        IMAGE_LOADED = 1

    def __init__(self):
        """
        Initialize the drift context with empty data.
        """
        self.observers : List[IObserver] = []

        self.image_state = self.ImageState.INIT

        # original frame
        self.gray : np.ndarray | None = None

        # smoothing error of profiles
        self.smooth_err = 21

        # restore true reference profile
        self.remove_sky : bool = True

        self.reference_ctx = MeanReferenceTrackContext()
        self.occultation_ctx = OccultationTrackContext()

        self.display_brightness = 0
        self.display_contrast = 1
        self.display_gamma = 1

        self.rect_width = 50
        self.rect_height = 100

    def update_rect_size(self, width : int, height : int):
        self.rect_width = width
        self.rect_height = height
        self.reference_ctx.update_rect_size(width, height)
        self.build_mean_reference_track()
        self.build_occultation_track()
        self.display_tracks()
        self.notify_observers()

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
        assert gray is not None
        self.gray = gray

        self.reference_ctx.set_image(gray)
        self.occultation_ctx.set_image(gray)
        self.rgb = cv2.cvtColor(self.gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        self.image_state = self.ImageState.IMAGE_LOADED
        self.notify_observers()

    def clear_image(self):
        self.reference_ctx.clear_image()
        self.occultation_ctx.clear_image()
        self.gray = None
        self.rgb = None
        self.image_state = self.ImageState.INIT
        self.notify_observers()

    def set_reference_half_w_cut(self, half_w : int):
        """
        Set the reference track half width value for track slices extraction.

        Parameters:
            half_w (int): New half width cut value.
        """
        self.reference_ctx.set_half_w_cut(half_w)
        self.notify_observers()
    
    def set_reference_half_w_profile(self, half_w : int):
        """
        Set the reference track half width value for track profile calculation.

        Parameters:
            half_w (int): New half width profile value.
        """
        self.reference_ctx.set_half_w_profile(half_w)
        self.notify_observers()

    def set_occultation_half_w_cut(self, half_w : int):
        """
        Set the occultation track half width value.

        Parameters:
            half_w (int): New half width value.
        """
        self.occultation_ctx.set_half_w_cut(half_w)
        self.notify_observers()

    def set_occultation_half_w_profile(self, half_w : int):
        """
        Set the occultation track half width value for track profile calculation.

        Parameters:
            half_w (int): New half width value.
        """
        self.occultation_ctx.set_half_w_profile(half_w)
        self.notify_observers()

    def display_tracks(self):
        """
        Display tracks in the drift context.
        """
        if self.image_state is self.ImageState.INIT:
            return

        assert self.gray is not None
        gray = (self.gray.astype(np.float32) - 127) * self.display_contrast + 127 + self.display_brightness * 127
        gray = np.clip(gray, 0, 255)
        self.rgb = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)

        # draw reference track line on each of reference tracks on original image
        for guid in self.reference_ctx.track_rects:
                reference_track_rect = self.reference_ctx.track_rects[guid]
                # draw track
                if self.reference_ctx.mean_track is not None:
                    reference_track_area, _ = reference_track_rect.extract_track(gray, 0)
                    reference_track = DriftTrack(reference_track_area,
                                                 margin=0,
                                                 path=self.reference_ctx.mean_track.path)

                    reference_track.draw_in_place(self.rgb,
                                                  reference_track_rect.left,
                                                  reference_track_rect.top,
                                                  (255,0,0),
                                                  (0,200,0),
                                                  0.5)

                    if guid in self.reference_ctx.labels:
                        x0 = reference_track_rect.left - 15
                        y0 = reference_track_rect.top - 2
                        cv2.putText(self.rgb, self.reference_ctx.labels[guid],
                                    (x0, y0), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0))

                # draw bounding rectangle
                cv2.rectangle(self.rgb, (reference_track_rect.left, reference_track_rect.top),
                                        (reference_track_rect.right, reference_track_rect.bottom),
                                        color=(255,0,0), thickness=1)

        # draw occultation track
        if self.occultation_ctx.profile_state in [OccultationTrackContext.ProfileState.REFERENCE_SPECIFIED,
                                                  OccultationTrackContext.ProfileState.PROFILE_BUILT]:
            assert self.occultation_ctx.track_rect is not None

            occultation_track_area, _ = self.occultation_ctx.track_rect.extract_track(self.gray, 0)

            if self.occultation_ctx.profile_state is OccultationTrackContext.ProfileState.PROFILE_BUILT:
                assert self.occultation_ctx.track is not None
                path = self.occultation_ctx.track.path
            else:
                assert self.reference_ctx.profile_state is MeanReferenceTrackContext.ProfileState.MEAN_TRACK
                assert self.reference_ctx.mean_track is not None
                path = self.reference_ctx.mean_track.path

            occultation_track = DriftTrack(occultation_track_area,
                                           margin=0,
                                           path=path)

            occultation_track.draw_in_place(self.rgb,
                                            self.occultation_ctx.track_rect.left,
                                            self.occultation_ctx.track_rect.top,
                                            (0,200,0), (0,200,0), 0.5)

            # draw bounding rectangles
            cv2.rectangle(self.rgb, (self.occultation_ctx.track_rect.left,
                                     self.occultation_ctx.track_rect.top),
                                    (self.occultation_ctx.track_rect.right,
                                     self.occultation_ctx.track_rect.bottom),
                                    color=(0,200,0), thickness=1)

            cv2.rectangle(self.rgb, (self.occultation_ctx.track_rect.left-self.occultation_ctx.margin,
                                     self.occultation_ctx.track_rect.top-self.occultation_ctx.margin),
                                    (self.occultation_ctx.track_rect.right+self.occultation_ctx.margin,
                                     self.occultation_ctx.track_rect.bottom+self.occultation_ctx.margin),
                                    color=(0,200,0), thickness=1)
        self.notify_observers()

    def draw_tracks(self):
        self.reference_ctx.draw_tracks()
        self.occultation_ctx.draw_track()
        self.display_tracks()

    def autodetect_tracks(self):
        """
        Detect tracks in the drift context.
        """
        self.reference_ctx.autodetect_tracks()
        if self.reference_ctx.profile_state is MeanReferenceTrackContext.ProfileState.RECTS_CONFIGURED:
            self.build_mean_reference_track()

        if self.reference_ctx.profile_state is MeanReferenceTrackContext.ProfileState.MEAN_TRACK:
            assert self.reference_ctx.mean_track is not None
            self.rect_width = self.reference_ctx.mean_track.w
            self.rect_height = self.reference_ctx.mean_track.h

        self.notify_observers()

    def build_mean_reference_track(self):
        """
        Build mean reference track in the drift context.
        """
        self.reference_ctx.build_mean_reference_track()
        if self.reference_ctx.profile_state is MeanReferenceTrackContext.ProfileState.MEAN_TRACK:
            assert self.reference_ctx.mean_track is not None
            self.occultation_ctx.specify_reference_track(self.reference_ctx.mean_track)
            self.build_occultation_track()
        else:
            self.occultation_ctx.clear_reference_track()
        # draw tracks
        self.draw_tracks()
        self.notify_observers()

    def build_occultation_track(self):
        """
        Build occultation track in the drift context.
        """
        if self.reference_ctx.profile_state is MeanReferenceTrackContext.ProfileState.MEAN_TRACK:
            assert self.reference_ctx.mean_track is not None
            self.occultation_ctx.specify_reference_track(self.reference_ctx.mean_track)
            self.occultation_ctx.build_occultation_profile(self.remove_sky)
        else:
            self.occultation_ctx.clear_reference_track()
        self.draw_tracks()
        self.notify_observers()

    def set_image_parameters(self, brightness, contrast):
        self.display_brightness = brightness
        self.display_contrast = contrast
        self.display_tracks()
        self.notify_observers()

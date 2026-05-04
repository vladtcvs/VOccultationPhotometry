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
    def __init__(self):
        """
        Initialize the drift context with empty data.
        """
        self.observers : List[IObserver] = []

        self.labels = []

        # original frame
        self.gray : np.ndarray = None

        # smoothing error of profiles
        self.smooth_err = 21

        # restore true reference profile
        self.remove_sky : bool = True

        self.reference_ctx = MeanReferenceTrackContext()
        self.occultation_ctx = OccultationTrackContext()

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

        w = gray.shape[1]
        h = gray.shape[0]

        self.reference_ctx.set_image(gray)
        self.occultation_ctx.set_image(gray)
        self.occultation_ctx.specify_track_pos(w//2, h//2)
        self.rgb = cv2.cvtColor(self.gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        self.notify_observers()

    def save_labels(self, labels : List[str]):
        self.labels = labels

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
        if self.gray is None:
            self.rgb = None
            return

        self.rgb = cv2.cvtColor(self.gray.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        # draw reference track line on each of reference tracks on original image
        for idx, reference_track_rect in enumerate(self.reference_ctx.track_rects):
                # draw track
                if self.reference_ctx.mean_track is not None:
                    reference_track_area, _ = reference_track_rect.extract_track(self.gray, 0)
                    reference_track = DriftTrack(reference_track_area,
                                                 margin=0,
                                                 path=self.reference_ctx.mean_track.path)

                    reference_track.draw_in_place(self.rgb,
                                                  reference_track_rect.left,
                                                  reference_track_rect.top,
                                                  (255,0,0),
                                                  (0,200,0),
                                                  0.5)

                    if idx < len(self.labels):
                        x0 = reference_track_rect.left - 15
                        y0 = reference_track_rect.top - 2
                        cv2.putText(self.rgb, self.labels[idx], (x0, y0), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0))

                # draw bounding rectangle
                cv2.rectangle(self.rgb, (reference_track_rect.left, reference_track_rect.top),
                                        (reference_track_rect.right, reference_track_rect.bottom),
                                        color=(255,0,0), thickness=1)

        # draw occultation track
        if self.occultation_ctx.track_rect is not None:
            if self.occultation_ctx.track is not None:
                occultation_track_area, _ = self.occultation_ctx.track_rect.extract_track(self.gray, 0)
                path = None
                if self.occultation_ctx.track is not None:
                    path = self.occultation_ctx.track.path
                elif self.reference_ctx.mean_track is not None:
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

    def detect_tracks(self):
        """
        Detect tracks in the drift context.
        """
        self.reference_ctx.autodetect_tracks()

        # draw track bounding rectangles
        self.draw_tracks()
        self.notify_observers()

    def build_mean_reference_track(self):
        """
        Build mean reference track in the drift context.
        """
        self.reference_ctx.build_mean_reference_track()
        self.occultation_ctx.specify_reference_track(self.reference_ctx.mean_track)
        # draw tracks
        self.draw_tracks()
        self.notify_observers()

    def specify_occultation_track(self, x0 : int, y0 : int):
        """
        Specify occultation track position in the drift context.

        Parameters:
            x0 (int): X-coordinate of the position.
            y0 (int): Y-coordinate of the position.
        """
        self.occultation_ctx.specify_track_pos(x0, y0)

    def build_occultation_track(self):
        """
        Build occultation track in the drift context.
        """
        self.occultation_ctx.build_occultation_profile(self.remove_sky)
        self.draw_tracks()
        self.notify_observers()

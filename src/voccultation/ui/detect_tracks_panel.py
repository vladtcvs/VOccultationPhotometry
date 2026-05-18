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

"""UI panel for detecting, editing, and managing reference/occultation tracks.

Implements DetectTracksPanel with image display, auto-detection, manual track
placement, zoom/contrast controls, and integration with the drift analysis context.
"""

import wx
import wx.lib.scrolledpanel as scrolled

from voccultation.model.data_context import DriftContext, IObserver
from voccultation.ui.image_adjust_panel import ImageAdjustPanel, EVT_IMAGE_ADJUST, EVT_ZOOM_ADJUST
from voccultation.ui.navigation_panel import EVT_NAVIGATION, NavigationPanel

from voccultation.ui.track_selector import EVT_OCCULTATION_TRACK_PRESSED
from voccultation.ui.track_selector import EVT_REFERENCE_TRACK_PRESSED
from voccultation.ui.track_selector import EVT_REMOVE_TRACK_PRESSED
from voccultation.ui.track_selector import EVT_TRACKS_UPDATED
from voccultation.ui.track_selector import TrackSelector

class DetectTracksPanel(wx.Panel, IObserver):
    """
    Panel for detecting and managing reference and occultation tracks.
    """
    def __init__(self, parent, context : DriftContext, status : wx.StaticText):
        """
        Initialize the DetectTracksPanel.

        Args:
            parent: The parent window.
            context (DriftContext): The data context.
            status (wx.StaticText): Status bar text control.
        """
        wx.Panel.__init__(self, parent)
        self.status = status
        self.context = context
        self.context.add_observer(self)
        self.active_reference_track : str | None = None

        self.context.zoom = 1

        self.pos_status = "x:N/A y:N/A"
        self.zoom_status = "zoom:100%"

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(main_sizer)

        # Image panel
        image_panel = scrolled.ScrolledPanel(self)
        image_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        image_panel.SetSizer(image_panel_sizer)
        image_panel.SetupScrolling(True, True)
        image_panel.SetAutoLayout(True)

        main_sizer.Add(image_panel, proportion=1, flag=wx.EXPAND)

        empty_img = wx.Image(600, 600)
        self.image_ctrl = wx.StaticBitmap(image_panel,
                                          wx.ID_ANY,
                                          wx.BitmapBundle.FromBitmap(wx.Bitmap(empty_img)))
        self.image_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_bitmap_click)
        self.image_ctrl.Bind(wx.EVT_MOTION, self.on_mouse_move)

        image_panel_sizer.Add(self.image_ctrl, proportion=1, flag=wx.ALL | wx.ALIGN_CENTER)

        # Controls
        ctl_sizer = wx.BoxSizer(wx.VERTICAL)
        ctl_panel = scrolled.ScrolledPanel(self)
        ctl_panel.SetupScrolling(False, True)
        ctl_panel.SetSizer(ctl_sizer)

        auto_detect_references = wx.Button(ctl_panel, label="Auto detect references")
        auto_detect_references.Bind(wx.EVT_BUTTON, self.on_auto_detect_tracks)
        ctl_sizer.Add(auto_detect_references, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        navigator = NavigationPanel(ctl_panel)
        navigator.Bind(EVT_NAVIGATION, self.on_navigate)
        ctl_sizer.Add(navigator, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)

        image_adjust = ImageAdjustPanel(ctl_panel)
        image_adjust.Bind(EVT_IMAGE_ADJUST, self.on_image_adjust)
        image_adjust.Bind(EVT_ZOOM_ADJUST, self.on_zoom_adjust)
        ctl_sizer.Add(image_adjust, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)

        # Tracks
        self.track_selector = TrackSelector(ctl_panel)
        self.track_selector.Bind(EVT_REMOVE_TRACK_PRESSED, self.on_remove_reference)
        self.track_selector.Bind(EVT_OCCULTATION_TRACK_PRESSED, self.on_select_occultation)
        self.track_selector.Bind(EVT_REFERENCE_TRACK_PRESSED, self.on_select_reference)
        self.track_selector.Bind(EVT_TRACKS_UPDATED, self.on_tracks_updated)
        ctl_sizer.Add(self.track_selector,  0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)

        add_new_reference = wx.Button(ctl_panel, label="New reference")
        add_new_reference.Bind(wx.EVT_BUTTON, self.on_add_new_reference)
        ctl_sizer.Add(add_new_reference, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        w_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ctl_sizer.Add(w_sizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(ctl_panel, label="W : ")
        w_sizer.Add(label)
        self.track_width_input = wx.SpinCtrl(ctl_panel, min=20, max=500)
        self.track_width_input.SetValue(str(self.context.rect_width))
        self.track_width_input.Bind(wx.EVT_SPINCTRL, self.on_track_dimensions)
        w_sizer.Add(self.track_width_input)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ctl_sizer.Add(h_sizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(ctl_panel, label="H : ")
        h_sizer.Add(label)
        self.track_height_input = wx.SpinCtrl(ctl_panel, min=20, max=500)
        self.track_height_input.SetValue(str(self.context.rect_height))
        self.track_height_input.Bind(wx.EVT_SPINCTRL, self.on_track_dimensions)
        h_sizer.Add(self.track_height_input)

        main_sizer.Add(ctl_panel, proportion=0, flag=wx.ALL | wx.EXPAND, border=8)

    def on_track_dimensions(self, _event):
        """
        Handle track dimension input changes.

        Args:
            event: The wx spin control event.
        """
        try:
            self.context.update_rect_size(int(self.track_width_input.GetValue()),
                                          int(self.track_height_input.GetValue()))
        except Exception as _e:
            pass

    def update_dimensions(self):
        """
        Update the track width/height input controls from context.
        """
        self.track_width_input.SetValue(str(self.context.rect_width))
        self.track_height_input.SetValue(str(self.context.rect_height))

    def on_select_reference(self, event):
        """
        Select a reference track for editing.

        Args:
            event: The custom event containing the GUID.
        """
        self.active_reference_track = event.guid

    def on_select_occultation(self, _event):
        """
        Select the occultation track for editing.

        Args:
            event: The custom event.
        """
        self.active_reference_track = None

    def on_remove_reference(self, event):
        """
        Remove a reference track.

        Args:
            event: The custom remove event containing the GUID.
        """
        guid = event.guid
        self.context.reference_ctx.remove_track(guid)
        self.track_selector.remove_reference_track(guid)
        self.Layout()

    def on_tracks_updated(self, _event):
        """
        Handle track list update event.

        Args:
            event: The custom tracks updated event.
        """
        for guid in self.context.reference_ctx.track_rects.keys():
            self.context.reference_ctx.assign_label(guid, self.track_selector.track_labels.guid_label(guid))
        self.context.build_mean_reference_track()

    def on_add_new_reference(self, _event):
        """
        Add a new reference track.

        Args:
            event: The wx button event.
        """
        if self.context.gray is None:
            return
        guid = self.track_selector.add_new_reference_track()
        label = self.track_selector.track_labels.guid_label(guid)
        self.context.reference_ctx.create_new_track(guid, label, self.context.rect_width, self.context.rect_height)
        self.Layout()
        self.active_reference_track = guid
        self.track_selector.select_guid_reference_track(guid)

    def _get_img_crds(self, event):
        """
        Convert mouse event coordinates to image coordinates.

        Args:
            event: The wx mouse event.

        Returns:
            Tuple[int, int] or (None, None): Image coordinates.
        """
        x, y = event.GetPosition()
        ctl_w, ctl_h = self.image_ctrl.GetSize()
        if self.context.rgb is not None:
            image_w = self.context.rgb.shape[1]
            image_h = self.context.rgb.shape[0]
            pad_x = max(0, (ctl_w-image_w)//2)
            pad_y = max(0, (ctl_h-image_h)//2)
            scroll_x, scroll_y = self.image_ctrl.GetPosition()
            x = x - scroll_x - pad_x
            y = y - scroll_y - pad_y
            x = int(x / self.context.zoom + 0.5)
            y = int(y / self.context.zoom + 0.5)
            if x >= 0 and y >= 0 and x < image_w and y < image_h:
                return x, y
        return None, None

    def update_status(self):
        """
        Update the status bar text.
        """
        self.status.SetLabel(f"{self.pos_status} {self.zoom_status}")

    def on_mouse_move(self, event):
        """
        Handle mouse movement over the image.

        Args:
            event: The wx mouse event.
        """
        x, y = self._get_img_crds(event)
        self.print_pos_status(x, y)
        self.update_status()

    def print_pos_status(self, x, y):
        """
        Update position status string.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
        """
        if x is None or y is None:
            self.pos_status = f"x:N/A y:N/A"
        else:
            self.pos_status = f"x:{x} y:{y}"

    def print_zoom_status(self, zoom : int):
        """
        Update zoom status string.

        Args:
            zoom (int): Current zoom level.
        """
        self.zoom_status = f"zoom:{zoom*100}%"

    def on_bitmap_click(self, event):
        """
        Handle click on the image bitmap.

        Args:
            event: The wx mouse event.
        """
        x, y = self._get_img_crds(event)
        if x is None or y is None:
            return

        if self.active_reference_track is None:
            self.context.occultation_ctx.specify_track_pos(x, y)
        else:
            self.context.reference_ctx.specify_track_pos(self.active_reference_track, x, y)
            self.context.build_mean_reference_track()

        self.context.display_tracks()

    def on_image_adjust(self, event):
        """
        Handle image brightness/contrast adjustment event.

        Args:
            event: The image adjust event.
        """
        brightness = event.brightness
        contrast = event.contrast
        self.context.set_image_parameters(brightness, contrast)

    def on_zoom_adjust(self, event):
        """
        Handle zoom adjustment event.

        Args:
            event: The zoom adjust event.
        """
        zoom = event.zoom
        self.print_zoom_status(zoom)
        self.context.set_zoom(zoom)
        self.update_status()

    def on_navigate(self, event):
        """
        Handle navigation (arrow) events.

        Args:
            event: The navigation event.
        """
        dx = event.dx
        dy = event.dy
        if self.active_reference_track is None:
            x, y = self.context.occultation_ctx.track_position()
            x, y = (x + dx, y + dy)
            self.context.occultation_ctx.specify_track_pos(x, y)
        else:
            x, y = self.context.reference_ctx.track_position(self.active_reference_track)
            x, y = (x + dx, y + dy)
            self.context.reference_ctx.specify_track_pos(self.active_reference_track, x, y)
            self.context.build_mean_reference_track()
        self.context.display_tracks()

    def on_auto_detect_tracks(self, _event):
        """
        Handle auto-detect tracks button press.

        Args:
            event: The wx button event.
        """
        self.track_selector.clear()
        if self.context.gray is None:
            return

        self.context.autodetect_tracks()

        for guid in self.context.reference_ctx.track_rects.keys():
            self.track_selector.add_new_reference_track(guid)

        for guid in self.context.reference_ctx.track_rects.keys():
            label = self.track_selector.track_labels.guid_label(guid)
            self.context.reference_ctx.assign_label(guid, label)

        self.Layout()
        self.context.build_mean_reference_track()
        self.context.build_occultation_track()
        self.update_dimensions()

    def update_image(self):
        """
        Update the displayed image from context.
        """
        if self.context.rgb is None:
            empty_img = wx.EmptyBitmap(600, 600)
            self.image_ctrl.SetBitmap(empty_img)
            self.Layout()
            self.Refresh()
            self.image_ctrl.Refresh()
            return
        height, width = self.context.rgb.shape[:2]
        if self.context.rgb is not None:
            data = self.context.rgb.tobytes()
            image = wx.Image(width, height)
            image.SetData(data)
            gray_bitmap = image.ConvertToBitmap()
            self.image_ctrl.SetBitmap(gray_bitmap)
            self.Layout()
            self.Refresh()
            self.image_ctrl.Refresh()

    def notify(self):
        """
        Observer notification to update the image.
        """
        self.update_image()

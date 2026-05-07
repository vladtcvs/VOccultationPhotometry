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

from typing import Dict, List
import wx
import wx.lib.scrolledpanel as scrolled

from voccultation.model.data_context import DriftContext, IObserver
from voccultation.ui.navigation_panel import EVT_NAVIGATION, NavigationPanel
from voccultation.ui.track_selector import EVT_OCCULTATION_TRACK_PRESSED, EVT_REFERENCE_TRACK_PRESSED, EVT_REMOVE_TRACK_PRESSED, EVT_TRACKS_UPDATED, TrackSelector

class DetectTracksPanel(wx.Panel, IObserver):
    def __init__(self, parent, context : DriftContext, status : wx.StaticText):
        wx.Panel.__init__(self, parent)
        self.status = status
        self.context = context
        self.context.add_observer(self)
        self.active_reference_track : str = None

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(main_sizer)

        # Image panel
        image_box = wx.StaticBox(self, wx.ID_ANY, label='Image')
        image_box_sizer = wx.BoxSizer(wx.VERTICAL)
        image_box.SetSizer(image_box_sizer)
        main_sizer.Add(image_box, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        image_panel = scrolled.ScrolledPanel(image_box)
        image_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        image_panel.SetSizer(image_panel_sizer)
        image_panel.SetupScrolling(True, True)

        image_box_sizer.Add(image_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)

        empty_img = wx.Image(600, 600)
        self.image_ctrl = wx.StaticBitmap(image_panel, wx.ID_ANY , wx.Bitmap(empty_img))
        self.image_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_bitmap_click)
        self.image_ctrl.Bind(wx.EVT_MOTION, self.on_mouse_move)

        image_panel_sizer.Add(self.image_ctrl, proportion=0, flag=wx.ALL | wx.EXPAND, border=0)

        # Controls
        ctl_sizer = wx.BoxSizer(wx.VERTICAL)
        ctl_panel = wx.Panel(self)
        ctl_panel.SetSizer(ctl_sizer)

        auto_detect_references = wx.Button(ctl_panel, label="Auto detect references")
        auto_detect_references.Bind(wx.EVT_BUTTON, self.AutoDetectTracks)
        ctl_sizer.Add(auto_detect_references, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        navigator = NavigationPanel(ctl_panel)
        navigator.Bind(EVT_NAVIGATION, self.OnNavigate)
        ctl_sizer.Add(navigator, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)

        # Tracks
        self.track_selector = TrackSelector(ctl_panel)
        self.track_selector.Bind(EVT_REMOVE_TRACK_PRESSED, self.RemoveReference)
        self.track_selector.Bind(EVT_OCCULTATION_TRACK_PRESSED, self.SelectOccultation)
        self.track_selector.Bind(EVT_REFERENCE_TRACK_PRESSED, self.SelectReference)
        self.track_selector.Bind(EVT_TRACKS_UPDATED, self.TracksUpdated)
        ctl_sizer.Add(self.track_selector,  0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)

        add_new_reference = wx.Button(ctl_panel, label="New reference")
        add_new_reference.Bind(wx.EVT_BUTTON, self.AddNewReference)
        ctl_sizer.Add(add_new_reference, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        w_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ctl_sizer.Add(w_sizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(ctl_panel, label="W : ")
        w_sizer.Add(label)
        self.track_width_input = wx.SpinCtrl(ctl_panel, min=20, max=500)
        self.track_width_input.SetValue(str(self.context.rect_width))
        self.track_width_input.Bind(wx.EVT_SPINCTRL, self.TrackDimensions)
        w_sizer.Add(self.track_width_input)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ctl_sizer.Add(h_sizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(ctl_panel, label="H : ")
        h_sizer.Add(label)
        self.track_height_input = wx.SpinCtrl(ctl_panel, min=20, max=500)
        self.track_height_input.SetValue(str(self.context.rect_height))
        self.track_height_input.Bind(wx.EVT_SPINCTRL, self.TrackDimensions)
        h_sizer.Add(self.track_height_input)

        main_sizer.Add(ctl_panel, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=8)

    def TrackDimensions(self, event):
        try:
            self.context.update_rect_size(int(self.track_width_input.GetValue()),
                                          int(self.track_height_input.GetValue()))
        except Exception as e:
            pass

    def update_dimensions(self):
        self.track_width_input.SetValue(str(self.context.rect_width))
        self.track_height_input.SetValue(str(self.context.rect_height))

    def SelectReference(self, event):
        self.active_reference_track = event.guid

    def SelectOccultation(self, event):
        self.active_reference_track = None

    def RemoveReference(self, event):
        guid = event.guid
        self.context.reference_ctx.remove_track(guid)
        self.track_selector.remove_reference_track(guid)
        self.Layout()

    def TracksUpdated(self, event):
        for guid in self.context.reference_ctx.track_rects.keys():
            self.context.reference_ctx.assign_label(guid, self.track_selector.track_labels.guid_label(guid))
        self.context.build_mean_reference_track()

    def AddNewReference(self, event):
        if self.context.gray is None:
            return
        guid = self.track_selector.add_new_reference_track()
        label = self.track_selector.track_labels.guid_label(guid)
        self.context.reference_ctx.create_new_track(guid, label, self.context.rect_width, self.context.rect_height)
        self.Layout()
        self.active_reference_track = guid
        self.track_selector.select_guid_reference_track(guid)

    def _get_img_crds(self, event):
        x, y = event.GetPosition()
        ctl_w, ctl_h = self.image_ctrl.GetSize()
        if self.context.gray is not None:
            image_w = self.context.gray.shape[1]
            image_h = self.context.gray.shape[0]
            pad_x = max(0, (ctl_w-image_w)//2)
            pad_y = max(0, (ctl_h-image_h)//2)
            scroll_x, scroll_y = self.image_ctrl.GetPosition()
            x = x - scroll_x - pad_x
            y = y - scroll_y - pad_y
            if x < 0 or y < 0 or x >= image_w or y >= image_h:
                x = None
                y = None
        else:
            x = None
            y = None
        return x, y

    def on_mouse_move(self, event):
        x, y = self._get_img_crds(event)
        if x is None or y is None:
            self.status.SetLabel("x:N/A y:N/A")
        else:
            self.status.SetLabel(f"x:{x} y:{y}")

    def on_bitmap_click(self, event):
        x, y = self._get_img_crds(event)
        if x is None or y is None:
            return

        if self.active_reference_track is None:
            self.context.occultation_ctx.specify_track_pos(x, y)
        else:
            self.context.reference_ctx.specify_track_pos(self.active_reference_track, x, y)
            self.context.build_mean_reference_track()

        self.context.display_tracks()

    def OnNavigate(self, event):
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

    def AutoDetectTracks(self, event):
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

    def UpdateImage(self):
        if self.context.gray is None:
            return
        height, width = self.context.gray.shape[:2]
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
        self.UpdateImage()

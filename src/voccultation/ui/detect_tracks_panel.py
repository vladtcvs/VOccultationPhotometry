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

import wx
import wx.lib.scrolledpanel as scrolled

from voccultation.model.data_context import DriftContext, IObserver
from voccultation.ui.navigation_panel import NavigationPanel
from voccultation.ui.track_selector import EVT_OCCULTATION_TRACK_PRESSED, EVT_REFERENCE_TRACK_PRESSED, EVT_REMOVE_TRACK_PRESSED, TrackSelector

class DetectTracksPanel(wx.Panel, IObserver):
    def __init__(self, parent, context : DriftContext, status : wx.StaticText):
        wx.Panel.__init__(self, parent)
        self.status = status
        self.context = context
        self.context.add_observer(self)
        self.active_reference_track : int = None
        self.active_occultation_track : bool = True

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
        navigator.add_observer(self)
        ctl_sizer.Add(navigator, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)

        # Tracks
        self.track_selector = TrackSelector(ctl_panel)
        self.track_selector.Bind(EVT_REMOVE_TRACK_PRESSED, self.RemoveReference)
        self.track_selector.Bind(EVT_OCCULTATION_TRACK_PRESSED, self.SelectOccultation)
        self.track_selector.Bind(EVT_REFERENCE_TRACK_PRESSED, self.SelectReference)
        ctl_sizer.Add(self.track_selector,  0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, border=10)

        add_new_reference = wx.Button(ctl_panel, label="New reference")
        add_new_reference.Bind(wx.EVT_BUTTON, self.AddNewReference)
        ctl_sizer.Add(add_new_reference, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)


        main_sizer.Add(ctl_panel, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=8)

    def SelectReference(self, event):
        guid = event.guid

    def SelectOccultation(self, event):
        pass

    def RemoveReference(self, event):
        guid = event.guid
        self.track_selector.remove_reference_track(guid)
        self.Layout()

    def AddNewReference(self, event):
        guid = self.track_selector.add_new_reference_track()
        self.Layout()

    def selectOccultation(self, event):
        self.active_occultation_track = True

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
        if x is not None and y is not None:
            self.context.specify_occultation_track(x, y)
            self.context.display_tracks()

    def navigate(self, dx, dy):
        x, y = self.occultation_track_position()
        x, y = (x + dx, y + dy)
        self.context.specify_occultation_track(x, y)
        self.context.display_tracks()

    def init_occultation_track_position(self):
        if self.context.gray is None:
            return
        w = self.context.gray.shape[1]
        h = self.context.gray.shape[0]
        rw = self.context.reference_ctx.mean_track.gray.shape[1]
        rh = self.context.reference_ctx.mean_track.gray.shape[0]
        y = int(h/2-rh/2)
        x = int(w/2-rw/2)
        self.context.occultation_track_pos = (y, x)

    def occultation_track_position(self):
        x = self.context.occultation_ctx.track_pos[1]
        y = self.context.occultation_ctx.track_pos[0]
        return x, y

    def AutoDetectTracks(self, event):
        self.context.detect_tracks()
        self.context.build_mean_reference_track()
        self.init_occultation_track_position()
        x, y = self.occultation_track_position()
        self.context.specify_occultation_track(x, y)
        self.context.build_occultation_track()

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

    def OnLoadImage(self):
        self.UpdateImage()

    def notify(self):
        self.UpdateImage()

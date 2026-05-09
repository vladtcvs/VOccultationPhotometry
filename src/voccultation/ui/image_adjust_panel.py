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
import wx.lib.newevent

ImageAdjustEvent, EVT_IMAGE_ADJUST = wx.lib.newevent.NewEvent()

class ImageAdjustPanel(wx.Panel):
    """
    Control for adjusting image brightness, contrast, gamma
    """

    def __init__(self, parent, id : int = wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)
        self.brighness = 0.0
        self.contrast = 1.0

        # Create sizer for layout
        sizer = wx.GridSizer(cols=2)

        # Brightness control

        brightness_label = wx.StaticText(self, label="Brightness:")
        self.brightness_ctl = wx.SpinCtrlDouble(self, min=-1, max=1, inc=0.1, value=f"{self.brighness}")
        self.brightness_ctl.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_brightness_change)
        sizer.Add(brightness_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizer.Add(self.brightness_ctl, 1, wx.EXPAND)

        # Contrast control
        contrast_label = wx.StaticText(self, label="Contrast:")
        self.contrast_ctl = wx.SpinCtrlDouble(self, min=0.1, max=8, inc=0.1, value=f"{self.contrast}")
        self.contrast_ctl.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_contrast_change)
        sizer.Add(contrast_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizer.Add(self.contrast_ctl, 1, wx.EXPAND)

        self.SetSizer(sizer)

    def on_brightness_change(self, event):
        self.brighness = self.brightness_ctl.GetValue()
        evt = ImageAdjustEvent(brightness=self.brighness, contrast=self.contrast)
        wx.PostEvent(self, evt)
        self.Layout()

    def on_contrast_change(self, event):
        self.contrast = self.contrast_ctl.GetValue()
        evt = ImageAdjustEvent(brightness=self.brighness, contrast=self.contrast)
        wx.PostEvent(self, evt)
        self.Layout()

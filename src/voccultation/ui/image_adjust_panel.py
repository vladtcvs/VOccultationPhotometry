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
        self.brighness = 0
        self.contrast = 0.1
        self.gamma = 1

        # Create sizer for layout
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Brightness control
        brightness_sizer = wx.BoxSizer(wx.HORIZONTAL)
        brightness_label = wx.StaticText(self, label="Brightness:")
        self.brightness_value = wx.StaticText(self, label="0")
        self.brightness_slider = wx.Slider(self, minValue=-100, maxValue=100, value=int(self.brighness*10), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.brightness_slider.Bind(wx.EVT_SLIDER, self.on_brightness_change)
        brightness_sizer.Add(brightness_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        brightness_sizer.Add(self.brightness_value, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        brightness_sizer.Add(self.brightness_slider, 1, wx.EXPAND)
        sizer.Add(brightness_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Contrast control
        contrast_sizer = wx.BoxSizer(wx.HORIZONTAL)
        contrast_label = wx.StaticText(self, label="Contrast:")
        self.contrast_value = wx.StaticText(self, label="0")
        self.contrast_slider = wx.Slider(self, minValue=1, maxValue=400, value=int(self.contrast*100), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.contrast_slider.Bind(wx.EVT_SLIDER, self.on_contrast_change)
        contrast_sizer.Add(contrast_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        contrast_sizer.Add(self.contrast_value, 00, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        contrast_sizer.Add(self.contrast_slider, 1, wx.EXPAND)
        sizer.Add(contrast_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Gamma control
        gamma_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gamma_label = wx.StaticText(self, label="Gamma:")
        self.gamma_value = wx.StaticText(self, label="1.00")
        self.gamma_slider = wx.Slider(self, minValue=1, maxValue=400, value=int(self.gamma*100), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.gamma_slider.Bind(wx.EVT_SLIDER, self.on_gamma_change)
        gamma_sizer.Add(gamma_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        gamma_sizer.Add(self.gamma_value, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        gamma_sizer.Add(self.gamma_slider, 1, wx.EXPAND)
        sizer.Add(gamma_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    def on_brightness_change(self, event):
        self.brighness = self.brightness_slider.GetValue() / 10.0
        self.brightness_value.SetLabel(str(self.brighness))
        evt = ImageAdjustEvent(brightness=self.brighness, contrast=self.contrast, gamma=self.gamma)
        wx.PostEvent(self, evt)

    def on_contrast_change(self, event):
        self.contrast = self.contrast_slider.GetValue() / 100.0
        self.contrast_value.SetLabel(f"{self.contrast:.2f}")
        evt = ImageAdjustEvent(brightness=self.brighness, contrast=self.contrast, gamma=self.gamma)
        wx.PostEvent(self, evt)

    def on_gamma_change(self, event):
        self.gamma = self.gamma_slider.GetValue() / 100.0
        self.gamma_value.SetLabel(f"{self.gamma:.2f}")
        evt = ImageAdjustEvent(brightness=self.brighness, contrast=self.contrast, gamma=self.gamma)
        wx.PostEvent(self, evt)

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

import csv
import wx
import wx.lib.scrolledpanel as scrolled

from voccultation.model.data_context import DriftContext, IObserver
from voccultation.ui.navigation_panel import NavigationPanel

class OccultationTrackPanel(wx.Panel):
    def __init__(self, parent, context : DriftContext):
        wx.Panel.__init__(self, parent)
        self.context = context
        self.context.add_observer(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(main_sizer)

        # track image panel
        track_box = wx.StaticBox(self, wx.ID_ANY, label='Track')
        track_sizer = wx.BoxSizer(wx.VERTICAL)
        track_box.SetSizer(track_sizer)
        main_sizer.Add(track_box, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        track_img = wx.Image(240, 480)
        self.track_image_ctrl = wx.StaticBitmap(track_box, wx.ID_ANY, wx.Bitmap(track_img))
        track_sizer.Add(self.track_image_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        # linear track image panel
        linear_track_img = wx.Image(480, 40)
        self.linear_track_image_ctrl = wx.StaticBitmap(track_box, wx.ID_ANY, wx.Bitmap(linear_track_img))
        track_sizer.Add(self.linear_track_image_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        # track plot panel
        plot_box = wx.StaticBox(self, wx.ID_ANY, label='Plot')
        plot_sizer = wx.BoxSizer(wx.VERTICAL)
        plot_box.SetSizer(plot_sizer)        
        main_sizer.Add(plot_box, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        empty_occ_profile_img = wx.Image(640,480)
        self.occ_profile_ctrl = wx.StaticBitmap(plot_box, wx.ID_ANY, wx.Bitmap(empty_occ_profile_img))
        plot_sizer.Add(self.occ_profile_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        # controls panel
        ctl_sizer = wx.BoxSizer(wx.VERTICAL)
        ctl_panel = wx.Panel(self)
        ctl_panel.SetSizer(ctl_sizer)

        plot_without_sky = wx.CheckBox(ctl_panel, label="Remove average sky value")
        plot_without_sky.SetValue(self.context.build_true_occ_profile)
        plot_without_sky.Bind(wx.EVT_CHECKBOX, self.PlotWithoutSky)
        ctl_sizer.Add(plot_without_sky, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        self.half_w_input = wx.TextCtrl(ctl_panel)
        self.half_w_input.SetValue(str(self.context.occ_half_w))
        self.half_w_input.Bind(wx.EVT_TEXT, self.SetOccHalfW)
        ctl_sizer.Add(self.half_w_input, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        build_mean_reference = wx.Button(ctl_panel, label="Analyze occultation track")
        build_mean_reference.Bind(wx.EVT_BUTTON, self.AnalyzeOccultation)
        ctl_sizer.Add(build_mean_reference, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        save_occultation = wx.Button(ctl_panel, label="Save occultation profile")
        save_occultation.Bind(wx.EVT_BUTTON, self.SaveOccultation)
        ctl_sizer.Add(save_occultation, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        navigator = NavigationPanel(ctl_panel)
        navigator.add_observer(self)
        ctl_sizer.Add(navigator, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        main_sizer.Add(ctl_panel, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=8)

    def PlotWithoutSky(self, event : wx.CommandEvent):
        self.context.build_true_occ_profile = event.IsChecked()

    def SetOccHalfW(self, event : wx.CommandEvent):
        text = event.GetString()
        try:
            value = int(text)
            self.context.set_occ_half_w(value)
        except Exception as e:
            pass

    def navigate(self, dx, dy):
        x = self.context.occ_track_pos[1]
        y = self.context.occ_track_pos[0]
        self.context.specify_occ_track(x + dx, y + dy)

    def AnalyzeOccultation(self, event):
        x = self.context.occ_track_pos[1]
        y = self.context.occ_track_pos[0]
        self.context.specify_occ_track(x, y)
        self.context.analyze_occ_track()

    def UpdateImage(self):
        if self.context.occ_track_rgb is not None:
            height, width = self.context.occ_track_rgb.shape[:2]
            data = self.context.occ_track_rgb.tobytes()
            image = wx.Image(width, height)
            image.SetData(data)
            gray_bitmap = image.ConvertToBitmap()
            self.track_image_ctrl.SetBitmap(gray_bitmap)
            self.track_image_ctrl.Refresh()

        if self.context.occ_profile_rgb is not None:
            height, width = self.context.occ_profile_rgb.shape[:2]
            data = self.context.occ_profile_rgb.tobytes()
            image = wx.Image(width, height)
            image.SetData(data)
            gray_bitmap = image.ConvertToBitmap()
            self.occ_profile_ctrl.SetBitmap(gray_bitmap)
            self.occ_profile_ctrl.Refresh()


        self.Layout()
        self.Refresh()

    def SaveOccultation(self, event):
        with wx.FileDialog(self, "Save occultation profile", wildcard="CSV (*.csv)|*.csv",style=wx.FD_SAVE) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = str(fileDialog.GetPath())
            if not pathname.endswith(".csv"):
                pathname = pathname + ".csv"
            
            with open(pathname, "w", encoding='utf8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'value', 'error'])
                ids = range(self.context.occ_profile.profile.shape[0])
                values = self.context.occ_profile.profile
                errors = self.context.occ_profile.error
                for index, value, error in zip(ids, values, errors):
                    writer.writerow([index, value, error])

    def notify(self):
        self.UpdateImage()
        self.half_w_input.ChangeValue(str(self.context.occ_half_w))

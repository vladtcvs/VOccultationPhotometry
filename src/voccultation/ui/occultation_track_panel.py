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
import imageio
import numpy as np
import wx

from voccultation.model.data_context import DriftContext, IObserver
from voccultation.ui.navigation_panel import EVT_NAVIGATION, NavigationPanel

class OccultationTrackPanel(wx.Panel, IObserver):
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

        # track slices
        self.track_slices_ctrl = wx.StaticBitmap(track_box, wx.ID_ANY, wx.Bitmap(wx.Image(480, 40)))
        track_sizer.Add(self.track_slices_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

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

        plot_without_sky = wx.CheckBox(ctl_panel, label="Remove sky value")
        plot_without_sky.SetValue(self.context.remove_sky)
        plot_without_sky.Bind(wx.EVT_CHECKBOX, self.PlotWithoutSky)
        ctl_sizer.Add(plot_without_sky, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(ctl_panel, label="Track half width:")
        ctl_sizer.Add(label, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        self.half_w_cut_input = wx.SpinCtrl(ctl_panel, min=1, max=100)
        self.half_w_cut_input.SetValue(str(self.context.occultation_ctx.half_w_cut))
        self.half_w_cut_input.Bind(wx.EVT_SPINCTRL, self.SetOccHalfW_Cut)
        ctl_sizer.Add(self.half_w_cut_input, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(ctl_panel, label="Track half width (used for profile):")
        ctl_sizer.Add(label, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        self.half_w_profile_input = wx.SpinCtrl(ctl_panel, min=1, max=100)
        self.half_w_profile_input.SetValue(str(self.context.occultation_ctx.half_w_profile))
        self.half_w_profile_input.Bind(wx.EVT_SPINCTRL, self.SetOccHalfW_Profile)
        ctl_sizer.Add(self.half_w_profile_input, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        build_mean_reference = wx.Button(ctl_panel, label="Analyze occultation track")
        build_mean_reference.Bind(wx.EVT_BUTTON, self.AnalyzeOccultation)
        ctl_sizer.Add(build_mean_reference, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        save_occultation_profile = wx.Button(ctl_panel, label="Save occultation profile")
        save_occultation_profile.Bind(wx.EVT_BUTTON, self.SaveOccultationProfile)
        ctl_sizer.Add(save_occultation_profile, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        save_occultation_slices = wx.Button(ctl_panel, label="Save occultation slices")
        save_occultation_slices.Bind(wx.EVT_BUTTON, self.SaveOccultationSlices)
        ctl_sizer.Add(save_occultation_slices, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        navigator = NavigationPanel(ctl_panel)
        navigator.Bind(EVT_NAVIGATION, self.OnNavigate)
        ctl_sizer.Add(navigator, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        main_sizer.Add(ctl_panel, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=8)

    def PlotWithoutSky(self, event : wx.CommandEvent):
        self.context.remove_sky = event.IsChecked()

    def SetOccHalfW_Cut(self, event : wx.CommandEvent):
        try:
            value = self.half_w_cut_input.GetValue()
            self.context.set_occultation_half_w_cut(value)
            self.context.build_occultation_track()
        except Exception as e:
            pass

    def SetOccHalfW_Profile(self, event : wx.CommandEvent):
        try:
            value = self.half_w_profile_input.GetValue()
            self.context.set_occultation_half_w_profile(value)
            self.context.build_occultation_track()
        except Exception as e:
            pass

    def OnNavigate(self, event):
        dx = event.dx
        dy = event.dy
        x, y = self.context.occultation_ctx.track_position()
        self.context.occultation_ctx.specify_track_pos(x + dx, y + dy)
        self.context.build_occultation_track()

    def AnalyzeOccultation(self, event):
        self.context.build_occultation_track()

    def UpdateImage(self):
        if self.context.occultation_ctx.image is not None:
            height, width = self.context.occultation_ctx.image.shape[:2]
            data = self.context.occultation_ctx.image.tobytes()
            image = wx.Image(width, height)
            image.SetData(data)
            gray_bitmap = image.ConvertToBitmap()
            self.track_image_ctrl.SetBitmap(gray_bitmap)
            self.track_image_ctrl.Refresh()

        if self.context.occultation_ctx.slices_image is not None:
            height, width = self.context.occultation_ctx.slices_image.shape[:2]
            
            occimg = self.context.occultation_ctx.slices_image.copy()
            occmarks = self.context.occultation_ctx.slices_marks

            idxs = np.where(np.sum(occmarks, axis=2) != 0)
            occimg[idxs] = occmarks[idxs]
            data = occimg.tobytes()

            image = wx.Image(width, height)
            image.SetData(data)
            gray_bitmap = image.ConvertToBitmap()
            self.track_slices_ctrl.SetBitmap(gray_bitmap)
            self.track_slices_ctrl.Refresh()

        if self.context.occultation_ctx.plot is not None:
            height, width = self.context.occultation_ctx.plot.shape[:2]
            data = self.context.occultation_ctx.plot.tobytes()
            image = wx.Image(width, height)
            image.SetData(data)
            gray_bitmap = image.ConvertToBitmap()
            self.occ_profile_ctrl.SetBitmap(gray_bitmap)
            self.occ_profile_ctrl.Refresh()

        self.Layout()
        self.Refresh()

    def SaveOccultationProfile(self, event):
        with wx.FileDialog(self, "Save occultation profile", wildcard="CSV (*.csv)|*.csv",style=wx.FD_SAVE) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = str(fileDialog.GetPath())
            if not pathname.endswith(".csv"):
                pathname = pathname + ".csv"

            with open(pathname, "w", encoding='utf8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'value', 'error'])
                ids = range(self.context.occultation_ctx.profile.profile.shape[0])
                values = self.context.occultation_ctx.profile.profile
                errors = self.context.occultation_ctx.profile.error
                for index, value, error in zip(ids, values, errors):
                    writer.writerow([index, value, error])

    def SaveOccultationSlices(self, event):
        with wx.FileDialog(self, "Save occultation slices", wildcard="PNG (*.png)|*.png",style=wx.FD_SAVE) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = str(fileDialog.GetPath())
            if not pathname.endswith(".png"):
                pathname = pathname + ".png"

            image = self.context.occultation_ctx.slices_image
            imageio.imwrite(pathname, image)

    def notify(self):
        self.UpdateImage()
        self.half_w_cut_input.SetValue(self.context.occultation_ctx.half_w_cut)
        self.half_w_profile_input.SetValue(self.context.occultation_ctx.half_w_profile)

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

"""UI panel for building and inspecting the mean reference track.

Provides ReferenceTrackPanel with track/slices visualization, orientation selection,
smoothing and half-width controls, profile plotting, and CSV/PNG export.
"""

import csv
import imageio
import numpy as np
import wx

from voccultation.methods.mean_reference_track import TrackOrientation
from voccultation.model.data_context import DriftContext, IObserver

class ReferenceTrackPanel(wx.Panel, IObserver):
    """
    Panel for building and displaying the mean reference track and profile.
    """
    def __init__(self, parent, context : DriftContext):
        """
        Initialize the ReferenceTrackPanel.

        Args:
            parent: The parent window.
            context (DriftContext): The data context for drift tracking.
        """
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
        self.ref_track_ctrl = wx.StaticBitmap(track_box,
                                              wx.ID_ANY,
                                              wx.BitmapBundle.FromBitmap(wx.Bitmap(track_img)))
        track_sizer.Add(self.ref_track_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        linear_track_img = wx.Image(480, 40)
        self.ref_track_slices_ctrl = wx.StaticBitmap(track_box,
                                                     wx.ID_ANY,
                                                     wx.BitmapBundle.FromBitmap(wx.Bitmap(linear_track_img)))
        track_sizer.Add(self.ref_track_slices_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        # track plot panel
        plot_box = wx.StaticBox(self, wx.ID_ANY, label='Plot')
        plot_sizer = wx.BoxSizer(wx.VERTICAL)
        plot_box.SetSizer(plot_sizer)        
        main_sizer.Add(plot_box, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        empty_occ_profile_img = wx.Image(640,480)
        self.ref_profile_ctrl = wx.StaticBitmap(plot_box,
                                                wx.ID_ANY,
                                                wx.BitmapBundle.FromBitmap(wx.Bitmap(empty_occ_profile_img)))
        plot_sizer.Add(self.ref_profile_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        # controls panel
        ctl_sizer = wx.BoxSizer(wx.VERTICAL)
        ctl_panel = wx.Panel(self)
        ctl_panel.SetSizer(ctl_sizer)

        # Track orientation control
        track_orientation_label = wx.StaticText(ctl_panel, wx.ID_ANY, label="Track orientation")
        ctl_sizer.Add(track_orientation_label, flag=wx.ALL, border=4)

        # Radio buttons for track orientation
        self.track_orientation_group = wx.RadioBox(ctl_panel, wx.ID_ANY, label="",
                                                   choices=["Automatic", "Horizontal", "Vertical"],
                                                   majorDimension=0,
                                                   style=wx.RA_SPECIFY_ROWS)
        self.track_orientation_group.SetSelection(0)  # Default to "Automatic"
        self.track_orientation_group.Bind(wx.EVT_RADIOBOX, self.on_select_orientation)
        ctl_sizer.Add(self.track_orientation_group, flag=wx.ALL | wx.EXPAND, border=4)

        label = wx.StaticText(ctl_panel, label="Reference track smooth:")
        ctl_sizer.Add(label, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        self.smooth_input = wx.SpinCtrl(ctl_panel, min=0, max=3)
        self.smooth_input.SetValue(str(self.context.reference_ctx.smooth))
        self.smooth_input.Bind(wx.EVT_SPINCTRL, self.on_set_smooth)
        ctl_sizer.Add(self.smooth_input, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(ctl_panel, label="Reference track half width:")
        ctl_sizer.Add(label, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        self.half_w_cut_input = wx.SpinCtrl(ctl_panel, min=2, max=100)
        self.half_w_cut_input.SetValue(str(self.context.reference_ctx.half_w_cut))
        self.half_w_cut_input.Bind(wx.EVT_SPINCTRL, self.on_set_ref_half_w_cut)
        ctl_sizer.Add(self.half_w_cut_input, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        label = wx.StaticText(ctl_panel, label="Reference track half width (used for profile):")
        ctl_sizer.Add(label, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        self.half_w_profile_input = wx.SpinCtrl(ctl_panel, min=1, max=100)
        self.half_w_profile_input.SetValue(str(self.context.reference_ctx.half_w_profile))
        self.half_w_profile_input.Bind(wx.EVT_SPINCTRL, self.on_set_ref_half_w_profile)
        ctl_sizer.Add(self.half_w_profile_input, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        build_mean_reference = wx.Button(ctl_panel, label="Build mean reference track")
        build_mean_reference.Bind(wx.EVT_BUTTON, self.on_build_mean_reference)
        ctl_sizer.Add(build_mean_reference, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        save_mean_reference = wx.Button(ctl_panel, label="Save reference profile")
        save_mean_reference.Bind(wx.EVT_BUTTON, self.on_save_reference)
        ctl_sizer.Add(save_mean_reference, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        save_reference_slices = wx.Button(ctl_panel, label="Save reference slices")
        save_reference_slices.Bind(wx.EVT_BUTTON, self.on_save_reference_slices)
        ctl_sizer.Add(save_reference_slices, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        main_sizer.Add(ctl_panel, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=8)

    def on_set_smooth(self, _event):
        """
        Handle the smooth input change event.

        Args:
            _event: The wx event (unused).
        """
        try:
            value = self.smooth_input.GetValue()
            self.context.reference_ctx.smooth = value
            self.context.build_mean_reference_track()
        except Exception as _e:
            pass

    def on_select_orientation(self, _event):
        """
        Handle the track orientation selection change.

        Args:
            _event: The wx event (unused).
        """
        selected = self.track_orientation_group.GetSelection()
        if selected == 0:
            self.context.reference_ctx.specify_track_orientation(None)
        elif selected == 1:
            self.context.reference_ctx.specify_track_orientation(TrackOrientation.TRACK_HORIZONTAL)
        elif selected == 2:
            self.context.reference_ctx.specify_track_orientation(TrackOrientation.TRACK_VERTICAL)
        self.context.build_mean_reference_track()
        self.context.build_occultation_track()

    def on_set_ref_half_w_cut(self, _event):
        """
        Handle the reference half-width cut change event.

        Args:
            _event: The wx event (unused).
        """
        try:
            value = self.half_w_cut_input.GetValue()
            self.context.set_reference_half_w_cut(value)
            self.context.build_mean_reference_track()
        except Exception as _e:
            pass
    
    def on_set_ref_half_w_profile(self, _event):
        """
        Handle the reference half-width profile change event.

        Args:
            _event: The wx event (unused).
        """
        try:
            value = self.half_w_profile_input.GetValue()
            self.context.set_reference_half_w_profile(value)
            self.context.build_mean_reference_track()
        except Exception as _e:
            pass

    def on_save_reference(self, _event):
        """
        Save the reference profile to a CSV file.

        Args:
            _event: The wx event (unused).
        """
        if self.context.reference_ctx.mean_profile is None:
            return
        with wx.FileDialog(self, "Save reference profile", wildcard="CSV (*.csv)|*.csv",style=wx.FD_SAVE) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = str(file_dialog.GetPath())
            if not pathname.endswith(".csv"):
                pathname = pathname + ".csv"
            with open(pathname, "w", encoding='utf8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'value', 'error'])
                ids = range(self.context.reference_ctx.mean_profile.profile.shape[0])
                values = self.context.reference_ctx.mean_profile.profile
                errors = self.context.reference_ctx.mean_profile.error
                for index, value, error in zip(ids, values, errors):
                    writer.writerow([index, value, error])

    def on_build_mean_reference(self, _event):
        """
        Build the mean reference track.

        Args:
            event: The wx event.
        """
        self.context.build_mean_reference_track()

    def update_image(self):
        """
        Update the displayed images for track, slices, and profile.
        """
        if self.context.reference_ctx.mean_image is not None:
            height, width = self.context.reference_ctx.mean_image.shape[:2]
            data = self.context.reference_ctx.mean_image.tobytes()
            image = wx.Image(width, height)
            image.SetData(data)
            gray_bitmap = image.ConvertToBitmap()
            self.ref_track_ctrl.SetBitmap(gray_bitmap)
            self.ref_track_ctrl.Refresh()

        if self.context.reference_ctx.mean_slices_image is not None:
            assert self.context.reference_ctx.mean_slices_marks is not None
            height, width = self.context.reference_ctx.mean_slices_image.shape[:2]
            refimg = self.context.reference_ctx.mean_slices_image.copy()
            refmarks = self.context.reference_ctx.mean_slices_marks
            idxs = np.where(np.sum(refmarks, axis=2) != 0)
            refimg[idxs] = refmarks[idxs]
            data = refimg.tobytes()
            image = wx.Image(width, height)
            image.SetData(data)
            gray_bitmap = image.ConvertToBitmap()
            self.ref_track_slices_ctrl.SetBitmap(gray_bitmap)
            self.ref_track_ctrl.Refresh()

        if self.context.reference_ctx.mean_plot is not None:
            height, width = self.context.reference_ctx.mean_plot.shape[:2]
            data = self.context.reference_ctx.mean_plot.tobytes()
            image = wx.Image(width, height)
            image.SetData(data)
            gray_bitmap = image.ConvertToBitmap()
            self.ref_profile_ctrl.SetBitmap(gray_bitmap)
            self.ref_profile_ctrl.Refresh()

        self.Layout()
        self.Refresh()

    def on_save_reference_slices(self, _event):
        """
        Save the reference slices image to a PNG file.

        Args:
            _event: The wx event (unused).
        """
        if self.context.reference_ctx.mean_slices_image is None:
            return
        with wx.FileDialog(self, "Save reference slices", wildcard="PNG (*.png)|*.png",style=wx.FD_SAVE) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = str(file_dialog.GetPath())
            if not pathname.endswith(".png"):
                pathname = pathname + ".png"

            image = self.context.reference_ctx.mean_slices_image
            imageio.imwrite(pathname, image)

    def notify(self):
        """
        Observer notification callback to update the panel.
        """
        self.update_image()
        self.half_w_cut_input.SetValue(self.context.reference_ctx.half_w_cut)
        self.half_w_profile_input.SetValue(self.context.reference_ctx.half_w_profile)
        self.smooth_input.SetValue(self.context.reference_ctx.smooth)

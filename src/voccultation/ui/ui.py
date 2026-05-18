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

"""Main application UI module.

Defines the DriftWindow class which hosts the notebook with DetectTracksPanel,
ReferenceTrackPanel, and OccultationTrackPanel, along with menu handling,
image loading, and about dialog.
"""

import wx
import wx.adv
import numpy as np
from PIL import Image

from voccultation.model.data_context import DriftContext
from voccultation.ui.detect_tracks_panel import DetectTracksPanel
from voccultation.ui.reference_track_panel import ReferenceTrackPanel
from voccultation.ui.occultation_track_panel import OccultationTrackPanel

VERSION="1.3"

class DriftWindow(wx.Frame):
    """
    Main application window containing the notebook with detection,
    reference, and occultation track panels.
    """
    def __init__(self, title : str, context : DriftContext):
        wx.Frame.__init__(self, None, title=title, size=wx.Size(1200,800))
        self.context = context
        self.Bind(wx.EVT_CLOSE, self.on_close)
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        m_open = file_menu.Append(wx.ID_OPEN, "Open\tCtrl-O", "Open tracks image")
        m_exit = file_menu.Append(wx.ID_EXIT, "Exit\tCtrl-Q", "Close window and exit program")
        self.Bind(wx.EVT_MENU, self.on_open_image, m_open)
        self.Bind(wx.EVT_MENU, self.on_close, m_exit)
        menu_bar.Append(file_menu, "&File")

        help_menu = wx.Menu()
        m_about = help_menu.Append(wx.ID_ABOUT, "About", "About")
        self.Bind(wx.EVT_MENU, self.on_about, m_about)
        menu_bar.Append(help_menu, "&Help")

        self.SetMenuBar(menu_bar)

        statusbar = wx.StatusBar(self)
        self.SetStatusBar(statusbar)
        self.status = wx.StaticText(statusbar, label="x:N/A y:N/A zoom:100%")

        panel = wx.Panel(self)
        self.notebook = wx.Notebook(panel)

        self.detect_tracks_panel = DetectTracksPanel(self.notebook, self.context, self.status)
        self.notebook.AddPage(self.detect_tracks_panel, "Detect tracks")

        self.reference_track_panel = ReferenceTrackPanel(self.notebook, self.context)
        self.notebook.AddPage(self.reference_track_panel, "Reference track")

        self.occultation_track_panel = OccultationTrackPanel(self.notebook, self.context)
        self.notebook.AddPage(self.occultation_track_panel, "Occultation track")

        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_notebook_changed)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)

        self.Layout()

    def on_notebook_changed(self, _event):
        """
        Handle notebook page change events.

        Args:
            _event: The notebook page changed event.
        """
        page = self.notebook.GetSelection()
        if page == 2:
            self.occultation_track_panel.on_analyze_occultation(None)
        if page != 0:
            self.status.SetLabel("x:N/A y:N/A")

    def on_about(self, _event):
        """
        Show the about dialog.

        Args:
            _event: The menu event.
        """
        about_info = wx.adv.AboutDialogInfo()
        about_info.SetName("VOccultation")
        about_info.SetVersion(f"Version: {VERSION}")
        about_info.SetDescription("Asteroid occultation processing")
        about_info.SetCopyright("Vladislav Tsendrovskii(C) 2026")
        about_info.SetLicense("GNU GPL v3")
        about_info.SetWebSite("https://github.com/vladtcvs/VOccultation")
        wx.adv.AboutBox(about_info)

    def on_open_image(self, _event):
        """
        Handle open image menu command.

        Args:
            _event: The menu event.
        """
        with wx.FileDialog(self,
                           "Open track file",
                           wildcard="Image (*.png;*.jpg)|*.png;*.jpg",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = file_dialog.GetPath()
            try:
                gray = np.array(Image.open(pathname).convert('L'))
                self.context.set_image(gray)
                self.detect_tracks_panel.track_selector.clear()
            except IOError:
                wx.LogError("Cannot open file '%s'." % pathname)

    def on_close(self, _event):
        """
        Handle window close event.

        Args:
            event: The close event.
        """
        self.Destroy()

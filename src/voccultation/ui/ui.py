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
import wx.adv
import numpy as np
from PIL import Image

from voccultation.model.data_context import DriftContext
from voccultation.ui.detect_tracks_panel import DetectTracksPanel
from voccultation.ui.reference_track_panel import ReferenceTrackPanel
from voccultation.ui.occultation_track_panel import OccultationTrackPanel

class DriftWindow(wx.Frame):
    def __init__(self, title : str, context : DriftContext):
        wx.Frame.__init__(self, None, title=title, size=(1200,800))
        self.context = context
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        menuBar = wx.MenuBar()

        fileMenu = wx.Menu()
        m_open = fileMenu.Append(wx.ID_OPEN, "Open\tCtrl-O", "Open tracks image")
        m_exit = fileMenu.Append(wx.ID_EXIT, "Exit\tCtrl-Q", "Close window and exit program")
        self.Bind(wx.EVT_MENU, self.OnOpenImage, m_open)
        self.Bind(wx.EVT_MENU, self.OnClose, m_exit)
        menuBar.Append(fileMenu, "&File")

        helpMenu = wx.Menu()
        m_about = helpMenu.Append(wx.ID_ABOUT, "About", "About")
        self.Bind(wx.EVT_MENU, self.OnAbout, m_about)
        menuBar.Append(helpMenu, "&Help")

        self.SetMenuBar(menuBar)

        panel = wx.Panel(self)
        self.notebook = wx.Notebook(panel)

        self.detectTracksPanel = DetectTracksPanel(self.notebook, self.context)
        self.notebook.AddPage(self.detectTracksPanel, "Detect tracks")

        self.referenceTrackPanel = ReferenceTrackPanel(self.notebook, self.context)
        self.notebook.AddPage(self.referenceTrackPanel, "Reference track")

        self.occultationTrackPanel = OccultationTrackPanel(self.notebook, self.context)
        self.notebook.AddPage(self.occultationTrackPanel, "Occultation track")

        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.NotebookChanged)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)
        self.Layout()

    def NotebookChanged(self, event):
        page = self.notebook.GetSelection()
        if page == 2:
            self.occultationTrackPanel.AnalyzeOccultation(None)

    def OnAbout(self, event):
        aboutInfo = wx.adv.AboutDialogInfo()
        aboutInfo.SetName("VOccultation")
        aboutInfo.SetVersion("Version: 0.4")
        aboutInfo.SetDescription("Asteroid occultation processing")
        aboutInfo.SetCopyright("Vladislav Tsendrovskii(C) 2026")
        aboutInfo.SetLicense("GNU GPL v3")
        aboutInfo.SetWebSite("https://github.com/vladtcvs/VOccultation")
        wx.adv.AboutBox(aboutInfo)

    def OnOpenImage(self, event):
        with wx.FileDialog(self,
                           "Open track file",
                           wildcard="Image (*.png;*.jpg)|*.png;*.jpg",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                gray = np.array(Image.open(pathname).convert('L'))
                self.context.set_image(gray)
            except IOError:
                wx.LogError("Cannot open file '%s'." % pathname)

    def OnClose(self, event):
        self.Destroy()

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
import uuid

# Define custom event types
OccultationPressedEvent, EVT_OCCULTATION_TRACK_PRESSED = wx.lib.newevent.NewEvent()
ReferencePressedEvent, EVT_REFERENCE_TRACK_PRESSED = wx.lib.newevent.NewEvent()
RemoveTrackPressedEvent, EVT_REMOVE_TRACK_PRESSED = wx.lib.newevent.NewEvent()

class TrackSelector(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.occultation_button = wx.Button(self, label="Occultation track")
        self.sizer.Add(self.occultation_button, proportion=0, flag=wx.ALL, border=8)
        self.reference_tracks = {}  # GUID -> (btn_ref, btn_remove, h_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_occultation_pressed, self.occultation_button)
        self.SetSizer(self.sizer)

    def on_occultation_pressed(self, event):
        wx.PostEvent(self, OccultationPressedEvent())

    def add_new_reference_track(self):
        guid = str(uuid.uuid4())
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_ref = wx.Button(self, label="Reference track")
        btn_remove = wx.Button(self, label="X")
        h_sizer.Add(btn_ref, proportion=0, flag=wx.ALL, border=8)
        h_sizer.Add(btn_remove, proportion=0, flag=wx.ALL, border=8)
        self.sizer.Add(h_sizer, proportion=0, flag=wx.ALL, border=0)
        self.reference_tracks[guid] = (btn_ref, btn_remove, h_sizer)
        self.Bind(wx.EVT_BUTTON, lambda e: self.on_reference_pressed(e, guid), btn_ref)
        self.Bind(wx.EVT_BUTTON, lambda e: self.on_remove_pressed(e, guid), btn_remove)
        self.Layout()
        return guid

    def on_reference_pressed(self, event, guid):
        evt = ReferencePressedEvent(guid=guid)
        wx.PostEvent(self, evt)

    def on_remove_pressed(self, event, guid):
        evt = RemoveTrackPressedEvent(guid=guid)
        wx.PostEvent(self, evt)

    def remove_reference_track(self, guid):
        if guid in self.reference_tracks:
            btn_ref, btn_remove, h_sizer = self.reference_tracks[guid]
            self.Unbind(wx.EVT_BUTTON, btn_ref)
            self.Unbind(wx.EVT_BUTTON, btn_remove)
            self.sizer.Remove(h_sizer)
            btn_ref.Destroy()
            btn_remove.Destroy()
            del self.reference_tracks[guid]
            self.Layout()

    def clear(self):
        for guid in list(self.reference_tracks.keys()):
            self.remove_reference_track(guid)

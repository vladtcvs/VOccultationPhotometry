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
TracksUpdated, EVT_TRACKS_UPDATED = wx.lib.newevent.NewEvent()

class LabelManager:
    def __init__(self):
        self.guids = {}

    def clear(self):
        self.guids.clear()

    def add_new_guid(self, guid : str) -> str:
        if guid in self.guids:
            return str(self.guids[guid])

        newid = len(self.guids)+1
        self.guids[guid] = newid
        return f"#{newid}"

    def remove_guid(self, guid : str):
        if guid not in self.guids:
            return

        id = self.guids[guid]
        for guid_it in self.guids.keys():
            if self.guids[guid_it] > id:
                self.guids[guid_it] -= 1
        del self.guids[guid]

    def guid_label(self, guid : str) -> str:
        return f"#{self.guids[guid]}"

class TrackSelector(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.active_guid : str = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.occultation_button = wx.Button(self, label="Occultation track")
        self.sizer.Add(self.occultation_button, proportion=0, flag=wx.ALL, border=8)
        self.reference_tracks = {}  # GUID -> (btn_ref, btn_remove, h_sizer)
        self.track_labels = LabelManager()
        self.Bind(wx.EVT_BUTTON, self.on_occultation_pressed, self.occultation_button)
        self.SetSizer(self.sizer)

        self.active_bmp = wx.Bitmap(16, 16)
        dc = wx.MemoryDC()
        dc.SelectObject(self.active_bmp)
        dc.SetBackground(wx.Brush(wx.WHITE))
        dc.Clear()
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(wx.Colour(0, 200, 0)))
        dc.DrawCircle(8, 8, 7)
        dc.SelectObject(wx.NullBitmap)
        mask = wx.Mask(self.active_bmp, wx.WHITE)
        self.active_bmp.SetMask(mask)

        self.non_active_bmp = wx.Bitmap(16, 16)
        dc.SelectObject(self.non_active_bmp)
        dc.SetBackground(wx.Brush(wx.WHITE))
        dc.Clear()
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(wx.Colour(127, 127, 127)))
        dc.DrawCircle(8, 8, 7)
        dc.SelectObject(wx.NullBitmap)
        mask = wx.Mask(self.non_active_bmp, wx.WHITE)
        self.non_active_bmp.SetMask(mask)

        self.occultation_button.SetBitmapLabel(self.active_bmp)
        self.active_guid = None

    def on_occultation_pressed(self, event):
        self.active_guid = None
        self.select_occultation_track()
        wx.PostEvent(self, OccultationPressedEvent())

    def select_guid_reference_track(self, guid):
        if guid in self.reference_tracks:
            for iter_guid in self.reference_tracks.keys():
                btn_ref, _, _ = self.reference_tracks[iter_guid]
                btn_ref : wx.Button = btn_ref
                if guid == iter_guid:
                    btn_ref.SetBitmapLabel(self.active_bmp)
                else:
                    btn_ref.SetBitmapLabel(self.non_active_bmp)
            self.occultation_button.SetBitmapLabel(self.non_active_bmp)

    def select_occultation_track(self):
        for iter_guid in self.reference_tracks.keys():
            btn_ref, _, _ = self.reference_tracks[iter_guid]
            btn_ref : wx.Button = btn_ref
            btn_ref.SetBitmapLabel(self.non_active_bmp)
        self.occultation_button.SetBitmapLabel(self.active_bmp)

    def add_new_reference_track(self, guid = None):
        if guid is None:
            guid = str(uuid.uuid4())
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        new_label = self.track_labels.add_new_guid(guid)
        btn_ref = wx.Button(self, label=f"Reference track {new_label}")
        btn_ref.SetBitmapLabel(self.non_active_bmp)
        btn_remove = wx.Button(self, label="X")
        h_sizer.Add(btn_ref, proportion=0, flag=wx.ALL, border=8)
        h_sizer.Add(btn_remove, proportion=0, flag=wx.ALL, border=8)
        self.sizer.Add(h_sizer, proportion=0, flag=wx.ALL, border=0)
        self.reference_tracks[guid] = (btn_ref, btn_remove, h_sizer)
        self.Bind(wx.EVT_BUTTON, lambda e: self.on_reference_pressed(e, guid), btn_ref)
        self.Bind(wx.EVT_BUTTON, lambda e: self.on_remove_pressed(e, guid), btn_remove)
        self.Layout()
        evt = TracksUpdated()
        wx.PostEvent(self, evt)
        return guid

    def on_reference_pressed(self, event, guid):
        evt = ReferencePressedEvent(guid=guid)
        self.select_guid_reference_track(guid)
        self.active_guid = guid
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

            self.track_labels.remove_guid(guid)
            for guid_it in self.reference_tracks:
                label = self.track_labels.guid_label(guid_it)
                btn_ref : wx.Button = self.reference_tracks[guid_it][0]
                btn_ref.SetLabel(f"Reference Track {label}")

            if self.active_guid == guid:
                self.active_guid = None
                self.select_occultation_track()
            self.Layout()
            wx.PostEvent(self, OccultationPressedEvent())
            evt = TracksUpdated()
            wx.PostEvent(self, evt)

    def clear(self):
        for guid in self.reference_tracks.keys():
            btn_ref, btn_remove, h_sizer = self.reference_tracks[guid]
            self.Unbind(wx.EVT_BUTTON, btn_ref)
            self.Unbind(wx.EVT_BUTTON, btn_remove)
            self.sizer.Remove(h_sizer)
            btn_ref.Destroy()
            btn_remove.Destroy()
        self.reference_tracks.clear()
        self.track_labels.clear()
        self.Layout()
        evt = TracksUpdated()
        wx.PostEvent(self, evt)

    def guids(self):
        return dict(self.reference_track_ids)

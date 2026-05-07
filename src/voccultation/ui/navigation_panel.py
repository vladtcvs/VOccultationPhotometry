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
NavigationEvent, EVT_NAVIGATION = wx.lib.newevent.NewEvent()

class NavigationPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        ctl_btn_sizer = wx.GridSizer(cols=3, rows=3, hgap=10, vgap=10)
        self.SetSizer(ctl_btn_sizer)

        self.held_x = 0
        self.held_y = 0
        self.repeat_delay = 20
        self.first_delay = 400
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

        size = wx.Size(32, 32)

        # Up arrow (top row, middle column: row 0, col 1)
        up_bitmap = wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_BUTTON, size)
        up_button = wx.BitmapButton(self, id=wx.ID_ANY, bitmap=up_bitmap, size=(40, 40))
        up_button.Bind(wx.EVT_LEFT_DOWN, self.on_up)
        up_button.Bind(wx.EVT_LEFT_UP, self.on_release)

        # Left arrow (middle row, left column: row 1, col 0)
        left_bitmap = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_BUTTON, size)
        left_button = wx.BitmapButton(self, id=wx.ID_ANY, bitmap=left_bitmap, size=(40, 40))
        left_button.Bind(wx.EVT_LEFT_DOWN, self.on_left)
        left_button.Bind(wx.EVT_LEFT_UP, self.on_release)

        # Right arrow (middle row, right column: row 1, col 2)
        right_bitmap = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_BUTTON, size)
        right_button = wx.BitmapButton(self, id=wx.ID_ANY, bitmap=right_bitmap, size=(40, 40))
        right_button.Bind(wx.EVT_LEFT_DOWN, self.on_right)
        right_button.Bind(wx.EVT_LEFT_UP, self.on_release)

        # Bottom arrow (bottom row, middle column: row 2, col 1)
        down_bitmap = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_BUTTON, size)
        down_button = wx.BitmapButton(self, id=wx.ID_ANY, bitmap=down_bitmap, size=(40, 40))
        down_button.Bind(wx.EVT_LEFT_DOWN, self.on_down)
        down_button.Bind(wx.EVT_LEFT_UP, self.on_release)

        # Row 0
        ctl_btn_sizer.Add((0, 0), 0, wx.EXPAND)  # Empty (row 0, col 0)
        ctl_btn_sizer.Add(up_button, 0, wx.ALIGN_CENTER)  # Up button (row 0, col 1)
        ctl_btn_sizer.Add((0, 0), 0, wx.EXPAND)  # Empty (row 0, col 2)

        # Row 1
        ctl_btn_sizer.Add(left_button, 0, wx.ALIGN_CENTER)  # Left button (row 1, col 0)
        ctl_btn_sizer.Add((0, 0), 0, wx.EXPAND)  # Empty (row 1, col 1)
        ctl_btn_sizer.Add(right_button, 0, wx.ALIGN_CENTER)  # Right button (row 1, col 2)

        # Row 2
        ctl_btn_sizer.Add((0, 0), 0, wx.EXPAND)  # Empty (row 2, col 0)
        ctl_btn_sizer.Add(down_button, 0, wx.ALIGN_CENTER)  # Bottom button (row 2, col 1)
        ctl_btn_sizer.Add((0, 0), 0, wx.EXPAND)  # Empty (row 2, col 2)

    def on_timer(self, event):
        if self.held_x != 0 or self.held_y != 0:
            self._notify()
            self.timer.Start(self.repeat_delay, oneShot=True)

    def on_up(self, event):
        self.held_x = 0
        self.held_y = -1
        self._notify()
        self.timer.Start(self.first_delay, oneShot=True)

    def on_left(self, event):
        self.held_x = -1
        self.held_y = 0
        self._notify()
        self.timer.Start(self.first_delay, oneShot=True)

    def on_right(self, event):
        self.held_x = 1
        self.held_y = 0
        self._notify()
        self.timer.Start(self.first_delay, oneShot=True)

    def on_down(self, event):
        self.held_x = 0
        self.held_y = 1
        self._notify()
        self.timer.Start(self.first_delay, oneShot=True)

    def on_release(self, event):
        self.held_x = 0
        self.held_y = 0

    def _notify(self):
        evt = NavigationEvent(dx=self.held_x, dy=self.held_y)
        wx.PostEvent(self, evt)

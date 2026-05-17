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

from voccultation.model.data_context import DriftContext
from voccultation.ui.ui import DriftWindow

import wx
import sys


def main():
    context = DriftContext()

    app = wx.App(redirect=False)
    top = DriftWindow(title="VOccultation", context=context)
    top.Show()
    app.MainLoop()
    sys.exit()

if __name__ == "__main__":
    main()

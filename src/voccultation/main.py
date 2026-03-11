from voccultation.model.data_context import DriftContext
from voccultation.ui.ui import DriftWindow

import wx
import sys


def main():
    context = DriftContext()

    app = wx.App(redirect=False)
    top = DriftWindow(title="VOccultationPhotometry", context=context)
    top.Show()
    app.MainLoop()
    sys.exit()

if __name__ == "__main__":
    main()

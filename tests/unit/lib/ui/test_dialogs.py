import os

import wx
from tatlin.lib.ui.dialogs import AboutDialog, OpenDialog, OpenErrorAlert, QuitDialog
from tatlin.lib.util import resolve_path
from tests.guitestcase import GUITestCase


class DialogsTest(GUITestCase):
    def test_open_dialog(self):
        dlg = OpenDialog(self.frame, os.getcwd())
        wx.CallLater(250, dlg.EndModal, wx.ID_CANCEL)
        dlg.get_path()
        dlg.get_type()
        dlg.Destroy()

    def test_quit_dialog(self):
        dlg = QuitDialog(self.frame)
        wx.CallLater(250, dlg.EndModal, wx.ID_SAVE)
        dlg.show()
        dlg.Destroy()

    def test_about_dialog(self):
        icon = wx.Icon(resolve_path("tatlin.png"), wx.BITMAP_TYPE_PNG)
        about = AboutDialog("1.0", icon, "")

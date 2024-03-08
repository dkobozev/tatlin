import unittest

import wx


class GUITestCase(unittest.TestCase):
    """Base class for GUI tests that sets up an app and a frame.

    @see: https://github.com/wxWidgets/Phoenix/blob/master/unittests/wtc.py
    """

    def setUp(self):
        self.app = wx.App()
        wx.Log.SetActiveTarget(wx.LogStderr())
        self.frame = wx.Frame(None)
        self.frame.Show()
        self.frame.PostSizeEvent()

    def tearDown(self):
        def _cleanup():
            for w in wx.GetTopLevelWindows():  # type: ignore
                if w:
                    if isinstance(w, wx.Dialog) and w.IsModal():
                        w.EndModal(wx.ID_CANCEL)
                        wx.CallAfter(w.Destroy)
                    else:
                        w.Close(force=True)
            wx.WakeUpIdle()

        timer = wx.PyTimer(_cleanup)
        timer.Start(100)
        self.app.MainLoop()
        del self.app

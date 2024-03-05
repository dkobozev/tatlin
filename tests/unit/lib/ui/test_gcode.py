import typing
import unittest
from unittest.mock import Mock

import wx

from tatlin.lib.gl.scene import Scene
from tatlin.lib.ui.gcode import GcodePanel


class GcodePanelTest(unittest.TestCase):
    def setUp(self):
        self.app = wx.App()
        self.frame = wx.Frame(None)

    def tearDown(self):
        wx.CallAfter(self.app.ExitMainLoop)
        self.app.MainLoop()

    def test_constructor(self):
        mock_scene = typing.cast(Scene, Mock())
        panel = GcodePanel(self.frame, mock_scene)

import typing
from unittest.mock import Mock

from tatlin.lib.gl.scene import Scene
from tatlin.lib.ui.gcode import GcodePanel
from tests.guitestcase import GUITestCase


class GcodePanelTest(GUITestCase):
    def test_constructor(self):
        mock_scene = typing.cast(Scene, Mock())
        panel = GcodePanel(self.frame, mock_scene)

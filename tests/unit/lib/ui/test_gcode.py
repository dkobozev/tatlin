from unittest.mock import Mock

from tatlin.lib.ui.gcode import GcodePanel
from tests.guitestcase import GUITestCase


class GcodePanelTest(GUITestCase):
    def setUp(self):
        super().setUp()

        # self.mock_scene = typing.cast(Scene, Mock())
        self.mock_scene = Mock()
        self.mock_scene.model.width = 100
        self.mock_scene.model.height = 100
        self.mock_scene.model.depth = 100
        self.mock_scene.model.scaling_factor = 1.0
        self.mock_scene.model.rotation_angle = {
            (0, 0, 1): 0,
            (0, 1, 0): 0,
            (1, 0, 0): 0,
        }

        self.panel = GcodePanel(self.frame, self.mock_scene)
        self.panel.connect_handlers()

    def test_connect_handlers(self):
        # calling it more than once should have no effect
        self.panel.connect_handlers()

    def test_on_slider_moved(self):
        self.panel.on_slider_moved(Mock())

    def test_on_arrows_toggled(self):
        self.panel.on_arrows_toggled(Mock())

    def test_on_reset_clicked(self):
        self.panel.on_reset_clicked(Mock())

    def test_on_set_model_clicked(self):
        mock = Mock()
        mock.GetEventObject.return_value.GetValue.return_value = True
        self.panel.on_set_mode(mock)

    def test_on_set_ortho(self):
        self.panel.on_set_ortho(Mock())

    def test_set_initial_values(self):
        self.panel.set_initial_values(10, 5, 100, 100, 100)
        self.panel.set_initial_values(0, 5, 100, 100, 100)

    def test_set_3d_view(self):
        self.panel.set_3d_view(True)
        self.panel.set_3d_view(False)

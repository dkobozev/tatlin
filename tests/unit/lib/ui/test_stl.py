from unittest.mock import Mock
from tatlin.lib.gl.model import Model

from tatlin.lib.ui.stl import StlPanel
from tests.guitestcase import GUITestCase


class StlPanelTest(GUITestCase):
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

        self.panel = StlPanel(self.frame, self.mock_scene)
        self.panel.connect_handlers()

    def test_connect_handlers(self):
        # calling it more than once should have no effect
        self.panel.connect_handlers()

    def test_scaling_factor_changed(self):
        self.panel.scaling_factor_changed(2.0)
        self.panel.scaling_factor_changed("asdf")

    def test_dimension_changed(self):
        self.panel.dimension_changed("width", 200)
        self.panel.dimension_changed("width", "asdf")

    def test_rotation_changed(self):
        self.panel.rotation_changed("x", 90)
        self.panel.rotation_changed("x", "asdf")

    def test_on_entry_x_focus_out(self):
        self.panel.on_entry_x_focus_out(Mock())

    def test_on_entry_y_focus_out(self):
        self.panel.on_entry_y_focus_out(Mock())

    def test_on_entry_z_focus_out(self):
        self.panel.on_entry_z_focus_out(Mock())

    def test_on_entry_factor_focus_out(self):
        self.panel.on_entry_factor_focus_out(Mock())

    def test_on_entry_rotate_x_focus_out(self):
        self.panel.on_entry_rotate_x_focus_out(Mock())

    def test_on_entry_rotate_y_focus_out(self):
        self.panel.on_entry_rotate_y_focus_out(Mock())

    def test_on_entry_rotate_z_focus_out(self):
        self.panel.on_entry_rotate_z_focus_out(Mock())

    def test_on_x_90_clicked(self):
        self.panel.on_x_90_clicked(Mock())

    def test_on_y_90_clicked(self):
        self.panel.on_y_90_clicked(Mock())

    def test_on_z_90_clicked(self):
        self.panel.on_z_90_clicked(Mock())

    def test_rotate_relative(self):
        self.panel.rotate_relative(Model.AXIS_X, 90)
        self.panel.rotate_relative(Model.AXIS_Y, 90)
        self.panel.rotate_relative(Model.AXIS_Z, 90)

    def test_set_initial_values(self):
        self.panel.set_initial_values(100, 100, 100, 100, 100)

    def test_on_center_clicked(self):
        self.panel.on_center_clicked(Mock())

    def test_on_reset_clicked(self):
        self.panel.on_reset_clicked(Mock())

    def test_on_set_ortho(self):
        self.panel.on_set_ortho(Mock())

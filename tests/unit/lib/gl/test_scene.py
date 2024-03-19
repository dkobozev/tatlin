import wx
from unittest.mock import Mock
from tatlin.lib.gl.boundingbox import BoundingBox
from tatlin.lib.gl.scene import Scene
from tests.guitestcase import GUITestCase


class SceneTest(GUITestCase):
    def setUp(self):
        super().setUp()
        self.scene = Scene(self.frame)

    def test_display(self):
        model = Mock()
        model.initialized = False

        self.scene.add_model(model)
        self.scene.add_supporting_actor(Mock())

        self.add_to_frame(self.scene)

    def test_display_ortho(self):
        model = Mock()
        model.initialized = False

        self.scene.add_model(model)
        self.scene.mode_ortho = True

        self.add_to_frame(self.scene)

    def test_clear(self):
        self.scene.clear()

    def test_button_press(self):
        self.scene.button_press(1, 1)

    def test_button_motion(self):
        self.scene.button_motion(1, 1, 1, 0, 0)
        self.scene.button_motion(1, 1, 0, 1, 0)
        self.scene.button_motion(1, 1, 0, 0, 1)

    def test_wheel_scroll(self):
        self.scene.wheel_scroll(1)
        self.scene.wheel_scroll(-1)

    def test_reset_view(self):
        self.scene.reset_view()
        self.scene.reset_view(True)

    def test_mode_2d(self):
        self.scene.mode_2d = True
        self.assertEqual(self.scene.mode_2d, True)
        self.scene.mode_2d = False
        self.assertEqual(self.scene.mode_2d, False)

    def test_mode_ortho(self):
        self.scene.mode_ortho = True
        self.assertEqual(self.scene.mode_ortho, True)
        self.scene.mode_ortho = False
        self.assertEqual(self.scene.mode_ortho, False)

    def test_rotate_view(self):
        self.scene.rotate_view(1, 1)

    def test_view_model_center(self):
        self.scene.model = Mock()
        self.scene.model.bounding_box = BoundingBox((1, 1, 1), (2, 3, 4))

        self.scene.view_model_center()

    def test_change_num_layers(self):
        self.scene.model = Mock()
        self.scene.change_num_layers(1)

    def test_scale_model(self):
        self.scene.model = Mock()
        self.scene.scale_model(1)

    def test_center_model(self):
        self.scene.model = Mock()
        self.scene.model.bounding_box = BoundingBox((1, 1, 1), (2, 3, 4))
        self.scene.center_model()

    def test_change_model_dimension(self):
        m = Mock()
        m.width = 1
        m.scaling_factor = 1
        self.scene.model = m

        self.scene.change_model_dimension("width", 1)

    def test_rotate_model(self):
        self.scene.model = Mock()
        self.scene.rotate_model(1, "x")

    def test_show_arrows(self):
        self.scene.model = Mock()
        self.scene.show_arrows(True)

    def test_model_modified(self):
        self.assertFalse(self.scene.model_modified)

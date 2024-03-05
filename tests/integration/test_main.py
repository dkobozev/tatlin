import unittest
from tatlin.conf.config import Config
from tatlin.lib.gl.platform import Platform
from tatlin.lib.gl.scene import Scene
from tatlin.lib.model import ModelLoader
from tatlin.lib.ui.dialogs import ProgressDialog
from tatlin.lib.ui.window import MainWindow

from tatlin.main import App


class MainTest(unittest.TestCase):
    def setUp(self):
        self.app = App()
        self.window = MainWindow(self.app)
        self.scene = Scene(self.window)
        self.scene.clear()

        self.config = Config(".asdf")

    def test_gcode(self):
        model_loader = ModelLoader("tests/fixtures/gcode/top.gcode")
        progress_dialog = ProgressDialog()
        model_loader.load(self.config, self.scene, progress_dialog)

        platform = Platform(100, 100)
        self.scene.add_supporting_actor(platform)

        self.scene.init()

        self.scene.change_num_layers(2)
        self.scene.show_arrows(True)

    def test_stl(self):
        model_loader = ModelLoader("tests/fixtures/stl/top.stl")
        progress_dialog = ProgressDialog()
        model_loader.load(self.config, self.scene, progress_dialog)

        self.scene.init()

        self.assertEqual(self.scene.model_modified, False)

        self.scene.center_model()
        self.scene.scale_model(1)
        self.scene.rotate_model(90, "x")
        self.scene.change_model_dimension("width", 1)

        self.assertEqual(self.scene.model_modified, True)

    def test_scene(self):
        self.scene.init()

        self.scene.button_press(0, 0)
        self.scene.button_motion(0, 0, 1, 0, 0)
        self.scene.button_motion(0, 1, 0, 1, 0)
        self.scene.button_motion(1, 1, 0, 0, 1)
        self.scene.wheel_scroll(-1)
        self.scene.reset_view()
        self.scene.reset_view(True)
        self.scene.rotate_view(0, 0)


if __name__ == "__main__":
    unittest.main()

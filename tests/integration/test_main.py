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

    def test_stl(self):
        model_loader = ModelLoader("tests/fixtures/stl/top.stl")
        progress_dialog = ProgressDialog()
        model_loader.load(self.config, self.scene, progress_dialog)


if __name__ == "__main__":
    unittest.main()

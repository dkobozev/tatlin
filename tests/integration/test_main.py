import unittest
from tatlin.conf.config import Config
from tatlin.lib.gl.platform import Platform
from tatlin.lib.gl.scene import Scene
from tatlin.lib.model import ModelLoader
from tatlin.lib.ui.dialogs import ProgressDialog
from tatlin.lib.ui.window import MainWindow

from tatlin.main import App


class MainTest(unittest.TestCase):
    # def setUp(self):
    #    self.app = App()

    @unittest.skip("needs an X Display to run")
    def test_gcode(self):
        app = App()
        window = MainWindow(app)
        scene = Scene(window)
        scene.clear()

        config = Config(".asdf")
        model_loader = ModelLoader("tests/fixtures/gcode/top.gcode")
        progress_dialog = ProgressDialog()
        model_loader.load(config, scene, progress_dialog)

    @unittest.skip("needs an X Display to run")
    def test_stl(self):
        app = App()
        window = MainWindow(app)
        scene = Scene(window)
        scene.clear()

        config = Config(".asdf")
        model_loader = ModelLoader("tests/fixtures/stl/top.stl")
        progress_dialog = ProgressDialog()
        model_loader.load(config, scene, progress_dialog)


if __name__ == "__main__":
    unittest.main()

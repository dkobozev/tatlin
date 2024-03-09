import unittest
from unittest.mock import Mock
from tatlin.conf.config import Config
from tatlin.lib.model import ModelLoader


class ModelLoaderTest(unittest.TestCase):
    def setUp(self):
        self.config = Config(".asdf")

    def test_gcode(self):
        model_loader = ModelLoader("tests/fixtures/gcode/top.gcode")
        model, Panel = model_loader.load(self.config, Mock(), Mock())

        self.assertAlmostEqual(model.width, 71.73, places=2)
        self.assertAlmostEqual(model.height, 14.4, places=2)
        self.assertAlmostEqual(model.depth, 117, places=2)

    def test_stl(self):
        model_loader = ModelLoader("tests/fixtures/stl/top.stl")
        model_loader.load(self.config, Mock(), Mock())

    def test_binary_stl(self):
        model_loader = ModelLoader("tests/fixtures/stl/cube-bin.stl")
        model_loader.load(self.config, Mock(), Mock())


if __name__ == "__main__":
    unittest.main()

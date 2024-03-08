import unittest
from unittest.mock import Mock, call
from tatlin.lib.model.gcode.loader import GcodeModelLoader


class GcodeModelLoaderTest(unittest.TestCase):
    def test_load(self):
        loader = GcodeModelLoader("tests/fixtures/gcode/top.gcode")

        self.assertEqual(loader.path, "tests/fixtures/gcode/top.gcode")
        self.assertEqual(loader.dirname, "tests/fixtures/gcode")
        self.assertEqual(loader.basename, "top.gcode")
        self.assertEqual(loader.extension, ".gcode")
        self.assertEqual(loader.filetype, "gcode")
        self.assertEqual(loader.size, 250980)

        config = Mock()
        config.read.call_args_list = [
            call("machine.platform_offset_x", float),
            call("machine.platform_offset_y", float),
            call("machine.platform_offset_z", float),
        ]
        config.read.return_value = 1
        loader.load(config, Mock(), Mock())

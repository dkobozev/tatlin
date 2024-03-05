import os
import tempfile
import unittest

from tatlin.conf.config import Config


class ConfigTest(unittest.TestCase):
    def test_read(self):
        with tempfile.NamedTemporaryFile("w") as fp:
            fp.write(
                """[general]
test = 1

[ui]
window_w = 640
window_h = 480
gcodes_2d = 0

[machine]
platform_w = 120
platform_d = 100
            """
            )
            fp.seek(0)

            config = Config(fp.name)

            self.assertEqual(config.read("general.test"), "1")
            self.assertEqual(config.read("test"), "1")

            self.assertEqual(config.read("ui.recent_files"), None)
            self.assertEqual(config.read("ui.window_w"), "640")
            self.assertEqual(config.read("ui.window_h"), "480")
            self.assertEqual(config.read("ui.gcode_2d"), False)

    def test_write(self):
        config = Config(os.path.join(tempfile.gettempdir(), "tatlin.conf"))
        config.write("new_section.window_w", 640)
        config.commit()

        with open(config.fname, "r") as fp:
            self.assertEqual(
                fp.read().strip(),
                "[new_section]\nwindow_w = 640",
            )

        os.remove(config.fname)

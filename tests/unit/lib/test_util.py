import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from tatlin.lib.util import format_status, get_recent_files, resolve_path


class UtilTest(unittest.TestCase):
    def test_resolve_path(self):
        self.assertEqual(resolve_path("/tmp/test"), "/tmp/test")

        with patch("sys.frozen", True, create=True), patch(
            "sys._MEIPASS", "/", create=True
        ):
            self.assertEqual(resolve_path("test"), "/tatlin/test")

    def test_format_status(self):
        self.assertEqual(format_status("hello", 10, 10), " hello (10.0B, 10 vertices)")
        self.assertEqual(format_status("hello", 1024, 1), " hello (1.0KB, 1 vertex)")
        self.assertEqual(
            format_status("hello", 1048576, 10), " hello (1.0MB, 10 vertices)"
        )
        self.assertEqual(
            format_status("hello", 1073741824, 10), " hello (1.0GB, 10 vertices)"
        )

    def test_get_recent_files(self):
        mock = Mock()
        mock.read.return_value = "/tmp/test.stl:/tmp/test2.stl0"
        # files that don't exist are not returned
        self.assertEqual(get_recent_files(mock), [])

        with tempfile.NamedTemporaryFile(suffix=".gcode") as f:
            mock.read.return_value = f.name
            self.assertEqual(
                get_recent_files(mock), [(os.path.basename(f.name), f.name, None)]
            )

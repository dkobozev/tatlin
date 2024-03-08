import unittest
from tatlin.lib.gl.util import compile_display_list, html_color, paginate


class UtilTest(unittest.TestCase):
    def test_compile_display_list(self):
        dl = compile_display_list(lambda x: x, 1)

    def test_paginate(self):
        paginated = paginate(list(range(10)), 3)
        self.assertListEqual(list(paginated), [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]])

    def test_html_color(self):
        self.assertEqual(html_color("#ff0000"), [1.0, 0, 0])
        self.assertEqual(html_color("ff0000"), [1.0, 0, 0])

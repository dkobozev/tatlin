import unittest
from tatlin.lib.parsers.gcode.parser import GcodeLexer


class GcodeLexerTest(unittest.TestCase):
    def setUp(self):
        self.lexer = GcodeLexer()

    def compare_output(self, line, expected):
        self.assertEqual(self.lexer.scan_line(line), expected)

    def test_empty(self):
        line = ""
        expected = ("", {}, "")
        self.compare_output(line, expected)

    def test_whitespace(self):
        line = "\t   "
        expected = ("", {}, "")
        self.compare_output(line, expected)

    def test_comments(self):
        comment1 = "; M107 ; turn fan off"
        expected = ("", {}, comment1)
        self.compare_output(comment1, expected)

        comment2 = "(**** begin homing ****)"
        expected = ("", {}, comment2)
        self.compare_output(comment2, expected)

        comment3 = comment2 + comment1
        expected = ("", {}, comment3)
        self.compare_output(comment3, expected)

    def test_no_args_no_comment(self):
        line = "G21"
        expected = (line, {}, "")
        self.compare_output(line, expected)

    def test_no_args(self):
        line = "G21 ; set units to millimeters"
        expected = ("G21", {}, "; set units to millimeters")
        self.compare_output(line, expected)

    def test_int_arg(self):
        line = "G92 E0 ; reset extrusion distance"
        expected = ("G92", {"E": 0}, "; reset extrusion distance")
        self.compare_output(line, expected)

    def test_multiple_args(self):
        line = "G1 X81.430 Y77.020 E1.08502 ; skirt"
        expected = ("G1", {"X": 81.43, "Y": 77.02, "E": 1.08502}, "; skirt")
        self.compare_output(line, expected)

    def test_slic3r_file(self):
        fname = "tests/data/gcode/slic3r.gcode"
        with open(fname, "r") as f:
            self.lexer.load(f)
        result = list(self.lexer.scan())

    def test_skeinforge_file(self):
        fname = "tests/data/gcode/top.gcode"
        with open(fname, "r") as f:
            self.lexer.load(f)
        result = list(self.lexer.scan())

    def test_string_input(self):
        s = """
        M108 S255 (set extruder speed to maximum)
        M104 S205 T0 (set extruder temperature)
        M109 S105 T0 (set heated-build-platform temperature)
        """
        self.lexer.load(s)
        result = list(self.lexer.scan())
        self.assertEqual(len(result), 3)


if __name__ == "__main__":
    unittest.main()

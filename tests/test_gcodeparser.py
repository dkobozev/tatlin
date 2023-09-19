import unittest
from libtatlin.gcodeparser import GcodeParser, GcodeLexer, Movement, ArgsDict


class GcodeParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = GcodeParser()
        self.lexer = GcodeLexer()

    def test_args_dict(self):
        xyz = (7.27, 2.67, 0.91)
        x, y, z = xyz

        args = ArgsDict({'X': x, 'Y': y})

        self.assertEqual(args['X'], x)
        self.assertEqual(args['Y'], y)
        self.assertIsNone(args['Z'])

    def test_command_coords(self):
        xyz = (7.27, 2.67, 0.91)
        x, y, z = xyz

        gcode = 'G1'
        args = ArgsDict({'X': x, 'Y': y, 'Z': z})
        coords = self.parser.command_coords(gcode, args, args)
        self.assertEqual(coords, xyz)

        gcode = ''
        coords = self.parser.command_coords(gcode, args, args)
        self.assertIsNone(coords)

    def test_set_flags(self):
        commands = (
            ('', ArgsDict(), '(<perimeter> outer )'),
            ('', ArgsDict(), '(<loop> outer )'),
            ('', ArgsDict(), '(</loop>)'),
            ('M101', ArgsDict(), ''),
            ('M103', ArgsDict(), ''),
            ('M101', ArgsDict(), ''),
        )
        for command in commands:
            self.parser.set_flags(command)

        flags = (Movement.FLAG_PERIMETER | Movement.FLAG_PERIMETER_OUTER |
                 Movement.FLAG_EXTRUDER_ON)
        self.assertEqual(self.parser.flags, flags)

    def test_parse(self):
        gcode = """
        G1 Z0.000 F12000.000 ; move to first layer
        G1 X78.810 Y79.100 ; move to first skirt point
        G1 F600.000 E1.00000 ; compensate retraction
        G1 X79.600 Y78.350 F1482.000 E1.02761 ; skirt
        """
        self.parser.load(gcode)
        result = self.parser.parse()

        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 3)

    def test_update_args(self):
        oldargs = ArgsDict({'X': 0, 'Y': 0, 'Z': 0, 'F': 12000, 'E': 0})
        args = self.parser.update_args(oldargs, {'X': 1, 'Y': 1})

        self.assertEqual(args['X'], 1)
        self.assertEqual(args['Y'], 1)
        self.assertEqual(args['F'], 12000)

    def test_parse_new_layer_from_z(self):
        gcode = """
        G1 X-1.06 Y13.12 Z0.00 F1440.0 E0.000
        G1 X-1.06 Y13.25 Z0.00 F1440.0 E0.025
        G1 X-1.06 Y13.37 Z0.00 F1440.0 E0.050
        M103
        G1 X-1.09 Y13.49 Z0.36 F1920.0 E0.075
        M101
        G1 X-2.84 Y13.3 Z0.36 F1920.0 E0.100
        """
        self.parser.load(gcode)
        result = self.parser.parse()

        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 3)
        self.assertEqual(len(result[1]), 2)

    def test_cura(self):
        gcode = """
        M117 Printing stuff now...
        """
        self.lexer.load(gcode)
        for command, args, comment in self.lexer.scan():
            self.assertEqual(command, 'M117')
            self.assertEqual(len(args), 0)
            self.assertEqual(comment.strip(), 'Printing stuff now...')


if __name__ == '__main__':
    unittest.main()

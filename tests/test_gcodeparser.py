import unittest
from libtatlin.gcodeparser import GcodeParser, Movement, ArgsDict


class GcodeParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = GcodeParser()

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
        coords = self.parser.command_coords(gcode, args)
        self.assertEqual(coords, xyz)

        gcode = ''
        coords = self.parser.command_coords(gcode, args)
        self.assertIn(None, coords)

    def test_is_new_layer(self):
        dst = (0, 0, 0)
        is_new_layer = self.parser.is_new_layer(dst, '', '')
        self.assertFalse(is_new_layer)

        is_new_layer = self.parser.is_new_layer(dst, '', '(<layer> 1.272 )')
        self.assertTrue(is_new_layer)

        self.parser.src = (0, 0, 0)
        dst = (0, 0, 0.2)
        is_new_layer = self.parser.is_new_layer(dst, 'G1', '')
        self.assertTrue(is_new_layer)

    def test_set_flags(self):
        commands = (
            ('',     ArgsDict(), '(<perimeter> outer )'),
            ('',     ArgsDict(), '(<loop> outer )'),
            ('',     ArgsDict(), '(</loop>)'),
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
        G1 Z0.400 F12000.000 ; move to next layer
        G1 X78.810 Y79.100 ; move to first skirt point
        G1 F600.000 E1.00000 ; compensate retraction
        G1 X79.600 Y78.350 F1482.000 E1.02761 ; skirt
        """
        self.parser.load(gcode)
        result = self.parser.parse()
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 1)

    def test_update_args(self):
        self.parser.prev_args = {'X': 0, 'Y': 0, 'F': 12000}
        args = self.parser.update_args({'X': 1, 'Y': 1})

        self.assertEqual(self.parser.prev_args['X'], 0)
        self.assertEqual(self.parser.prev_args['Y'], 0)
        self.assertEqual(self.parser.prev_args['F'], 12000)

        self.assertEqual(args['X'], 1)
        self.assertEqual(args['Y'], 1)
        self.assertEqual(args['F'], 12000)

    def test_parse_new_layer_from_z(self):
        gcode = """
        G1 X-1.06 Y13.13 Z0.91 F1440.0
        G1 X-1.06 Y13.18 Z0.91 F1440.0
        M103
        G1 X-1.09 Y13.49 Z1.27 F1920.0
        M101
        G1 X-2.84 Y13.3 Z1.27 F1920.0
        """
        self.parser.load(gcode)
        result = self.parser.parse()
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(len(result[1]), 1)

if __name__ == '__main__':
    unittest.main()

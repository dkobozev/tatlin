import unittest
from libtatlin.gcodeparser2 import GcodeParser, Movement


class GcodeParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = GcodeParser()

    def test_command_coords(self):
        xyz = (7.27, 2.67, 0.91)
        x, y, z = xyz

        command = ('G1', {'X': x, 'Y': y, 'Z': z}, '')
        coords = self.parser.command_coords(command)
        self.assertEqual(coords, xyz)

        command = ('', {'X': x, 'Y': y, 'Z': z}, '')
        coords = self.parser.command_coords(command)
        self.assertFalse(coords)

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
            ('', {}, '(<perimeter> outer )'),
            ('', {}, '(<loop> outer )'),
            ('', {}, '(</loop>)'),
            ('M101', {}, ''),
            ('M103', {}, ''),
            ('M101', {}, ''),
        )
        for command in commands:
            self.parser.set_flags(command)

        flags = (Movement.FLAG_PERIMETER | Movement.FLAG_PERIMETER_OUTER |
                 Movement.FLAG_EXTRUDER_ON)
        self.assertEqual(self.parser.flags, flags)

    def test_parse(self):
        pass


if __name__ == '__main__':
    unittest.main()

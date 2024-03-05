import unittest

from tatlin.lib.gl.boundingbox import BoundingBox


class BoundingBoxTest(unittest.TestCase):
    def test_boundingbox(self):
        bb = BoundingBox((1, 1, 1), (2, 3, 4))

        self.assertEqual(bb.width, 1)
        self.assertEqual(bb.depth, 2)
        self.assertEqual(bb.height, 3)

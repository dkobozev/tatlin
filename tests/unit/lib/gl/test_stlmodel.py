import numpy

from tatlin.lib.gl.model import Model
from tatlin.lib.gl.scene import Scene
from tatlin.lib.gl.stlmodel import StlModel

from tests.guitestcase import GUITestCase


class StlModelTest(GUITestCase):
    def setUp(self):
        super().setUp()

        self.model = StlModel()
        self.model.load_data(
            [
                [[0, 0.5, 0], [0.5, -0.5, 0], [-0.5, -0.5, 0]],
                [[0, 0, 1], [0, 0, 1], [0, 0, 1]],
            ]
        )

    def test_normal_data_empty(self):
        self.assertFalse(self.model.normal_data_empty())

    def test_calculate_normals(self):
        normals = self.model.calculate_normals()
        numpy.testing.assert_array_almost_equal(
            normals,
            numpy.array([[0, 0, -1], [0, 0, -1], [0, 0, -1]], dtype=numpy.float32),
        )

    def test_init(self):
        self.model.init()
        self.assertTrue(self.model.initialized)

    def test_display(self):
        scene = Scene(self.frame)
        scene.add_model(self.model)
        self.add_to_frame(scene)

    def test_scale(self):
        self.assertFalse(self.model.modified)
        self.model.scale(1.1)
        self.assertTrue(self.model.modified)

    def test_translate(self):
        self.assertFalse(self.model.modified)
        self.model.translate(1, 2, 3)
        self.assertTrue(self.model.modified)

    def test_rotate_rel(self):
        self.assertFalse(self.model.modified)
        self.model.rotate_rel(90, Model.AXIS_X)
        self.assertTrue(self.model.modified)

    def test_rotate_abs(self):
        self.assertFalse(self.model.modified)
        self.model.rotate_abs(90, Model.AXIS_X)
        self.assertTrue(self.model.modified)

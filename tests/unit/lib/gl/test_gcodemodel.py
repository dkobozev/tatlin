import array

from tatlin.lib.gl.scene import Scene
from tatlin.lib.gl.gcodemodel import GcodeModel

from tatlin.lib.model.gcode.parser import Movement
from tests.guitestcase import GUITestCase


class GcodeModelTest(GUITestCase):
    def setUp(self):
        super().setUp()

        self.model = GcodeModel()
        self.model.load_data(
            [
                [
                    Movement(array.array("f", [0, 0.5, 0]), 0, 0, 0),
                    Movement(array.array("f", [0.5, -0.5, 0]), 0, 0, 0),
                    Movement(array.array("f", [-0.5, -0.5, 0]), 0, 0, 0),
                ]
            ]
        )

    def test_display(self):
        scene = Scene(self.frame)
        scene.add_model(self.model)
        self.add_to_frame(scene)

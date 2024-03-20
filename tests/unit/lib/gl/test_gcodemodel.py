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
                    Movement(
                        array.array("f", [-0.5, -0.5, 0]),
                        0,
                        0,
                        Movement.FLAG_EXTRUDER_ON | Movement.FLAG_PERIMETER,
                    ),
                ],
                [
                    Movement(array.array("f", [0, 0.5, 1.0]), 0, 0, 0),
                    Movement(array.array("f", [0.5, -0.5, 1.0]), 0, 0, 0),
                    Movement(array.array("f", [-0.5, -0.5, 1.0]), 0, 0, 0),
                ],
            ]
        )

    def test_display(self):
        scene = Scene(self.frame)
        scene.add_model(self.model)
        self.add_to_frame(scene)

    def test_display_layers_reverse(self):
        """Force the layers to be drawn in reverse order, top to bottom by raising the model."""
        scene = Scene(self.frame)
        scene.add_model(self.model)
        self.model.offset_z = 100
        self.add_to_frame(scene)

    def test_display_2d(self):
        scene = Scene(self.frame)
        scene.add_model(self.model)
        scene.mode_2d = True
        self.add_to_frame(scene)

    def test_display_ortho(self):
        scene = Scene(self.frame)
        scene.add_model(self.model)
        scene.mode_ortho = True
        self.add_to_frame(scene)

    def test_display_ortho_reverse(self):
        scene = Scene(self.frame)
        scene.add_model(self.model)
        scene.mode_ortho = True
        scene.rotate_view(0, 90)  # view from the bottom
        self.add_to_frame(scene)

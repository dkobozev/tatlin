import logging

from tatlin.lib.gl.gcodemodel import GcodeModel
from tatlin.lib.ui.gcode import GcodePanel

from ..baseloader import BaseModelLoader, ModelFileError
from .parser import GcodeParser, GcodeParserError


class GcodeModelLoader(BaseModelLoader):
    def load(self, config, scene, progress_dlg):
        parser = GcodeParser()
        with open(self.path, "r") as gcodefile:
            parser.load(gcodefile)
            try:
                progress_dlg.stage("Reading file...")
                data = parser.parse(progress_dlg.step)

                progress_dlg.stage("Loading file...")
                model = GcodeModel()
                model.load_data(data, progress_dlg.step)

                scene.add_model(model)
                scene.mode_2d = bool(config.read("ui.gcode_2d", int))

                offset_x = config.read("machine.platform_offset_x", float)
                offset_y = config.read("machine.platform_offset_y", float)
                offset_z = config.read("machine.platform_offset_z", float)

                if offset_x is None and offset_y is None and offset_z is None:
                    scene.view_model_center()
                    logging.info(
                        "Platform offsets not set, showing model in the center"
                    )
                else:
                    model.offset_x = offset_x if offset_x is not None else 0
                    model.offset_y = offset_y if offset_y is not None else 0
                    model.offset_z = offset_z if offset_z is not None else 0
                    logging.info(
                        "Using platform offsets: (%s, %s, %s)"
                        % (model.offset_x, model.offset_y, model.offset_z)
                    )
                return model, GcodePanel
            except GcodeParserError as e:
                # rethrow as generic file error
                raise ModelFileError(f"Parsing error: {e}")

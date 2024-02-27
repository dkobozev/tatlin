from abc import ABC, abstractmethod
import logging
import os

from tatlin.lib.gl.gcodemodel import GcodeModel
from tatlin.lib.gl.stlmodel import StlModel
from tatlin.lib.parsers.gcode.parser import GcodeParser, GcodeParserError

from tatlin.lib.parsers.stl.parser import StlParseError, StlParser
from tatlin.lib.ui.dialogs import ProgressDialog
from tatlin.lib.ui.gcode import GcodePanel
from tatlin.lib.ui.stl import StlPanel


class ModelFileError(Exception):
    pass


class BaseModelLoader(ABC):
    def __init__(self, path, ftype=None):
        self._path = path
        self._ftype = ftype
        self._reset_file_attributes()

    def _reset_file_attributes(self):
        self._dirname = None
        self._basename = None
        self._extension = None
        self._size = None

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._reset_file_attributes()
        self._path = path

    @property
    def dirname(self):
        if self._dirname is None:
            self._dirname = os.path.dirname(self.path)
        return self._dirname

    @property
    def basename(self):
        if self._basename is None:
            self._basename = os.path.basename(self.path)
        return self._basename

    @property
    def extension(self):
        if self._extension is None:
            self._extension = os.path.splitext(self.basename)[-1].lower()
        return self._extension

    @property
    def filetype(self):
        """
        Determine filetype based on extension.
        """
        if self._ftype is None:
            self._ftype = determine_filetype(self._path)
        return self._ftype

    @property
    def size(self):
        """
        File size in bytes.
        """
        if self._size is None:
            self._size = os.path.getsize(self.path)
        return self._size

    @abstractmethod
    def load(self, scene, read_cb, load_cb):
        pass


def determine_filetype(fpath):
    ext = os.path.splitext(fpath)[-1].lower()

    if ext not in [".gcode", ".nc", ".stl"]:
        raise ModelFileError(f"Unsupported file extension: {ext}")

    return "gcode" if ext in (".gcode", ".nc") else "stl"


class STLModelLoader(BaseModelLoader):
    def load(self, config, scene, progress_dlg):
        with open(self.path, "rb") as stlfile:
            parser = StlParser(stlfile)
            parser.load(stlfile)
            try:
                progress_dlg.stage("Reading file...")
                data = parser.parse(progress_dlg.step)

                progress_dlg.stage("Loading model...")
                model = StlModel()
                model.load_data(data, progress_dlg.step)

                scene.add_model(model)
                scene.mode_2d = False

                return model, StlPanel
            except StlParseError as e:
                # rethrow as generic file error
                raise ModelFileError(f"Parsing error: {e}")

    # @todo: move to a separate class
    def write_stl(self, stl_model):
        assert self.filetype == "stl"

        vertices, normals = stl_model.vertices, stl_model.normals

        f = open(self.path, "w")
        print("solid", file=f)
        print(
            "".join(
                [
                    self._format_facet(vertices[i : i + 3], normals[i])
                    for i in range(0, len(vertices), 3)
                ]
            ),
            file=f,
        )
        print("endsolid", file=f)
        f.close()

    def _format_facet(self, vertices, normal):
        template = """facet normal %.6f %.6f %.6f
  outer loop
    %s
  endloop
endfacet
"""
        stl_facet = template % (
            normal[0],
            normal[1],
            normal[2],
            "\n".join(["vertex %.6f %.6f %.6f" % (v[0], v[1], v[2]) for v in vertices]),
        )
        return stl_facet


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


def ModelLoader(fpath):
    ftype = determine_filetype(fpath)

    loader = None

    if ftype == "gcode":
        loader = GcodeModelLoader
    else:
        loader = STLModelLoader

    return loader(fpath, ftype)

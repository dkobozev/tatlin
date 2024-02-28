from tatlin.lib.gl.stlmodel import StlModel
from tatlin.lib.ui.stl import StlPanel

from ..baseloader import BaseModelLoader, ModelFileError
from .parser import StlParseError, StlParser


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

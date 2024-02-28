from .baseloader import determine_filetype, ModelFileError  # pass-thru import
from .gcode.loader import GcodeModelLoader
from .stl.loader import STLModelLoader


def ModelLoader(fpath):
    ftype = determine_filetype(fpath)

    loader = None

    if ftype == "gcode":
        loader = GcodeModelLoader
    else:
        loader = STLModelLoader

    return loader(fpath, ftype)

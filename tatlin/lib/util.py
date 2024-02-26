import os
import os.path
import sys
from tatlin.lib.constants import RECENT_FILE_LIMIT

from tatlin.lib.ui.dialogs import OpenDialog


def format_float(f):
    return "%.2f" % f


def resolve_path(fpath):
    if os.path.isabs(fpath):
        return fpath

    if getattr(sys, "frozen", False):
        # we are running in a PyInstaller bundle
        basedir = os.path.join(sys._MEIPASS, "tatlin")  # type:ignore
    else:
        # we are running in a normal Python environment
        basedir = os.path.dirname(os.path.dirname(__file__))

    return os.path.join(basedir, fpath)


def format_status(name, size_bytes, vertex_count):
    if size_bytes > 2**30:
        size = size_bytes / 2**30
        units = "GB"
    elif size_bytes > 2**20:
        size = size_bytes / 2**20
        units = "MB"
    elif size_bytes > 2**10:
        size = size_bytes / 2**10
        units = "KB"
    else:
        size = size_bytes
        units = "B"

    vertex_plural = "vertex" if int(str(vertex_count)[-1]) == 1 else "vertices"

    return " %s (%.1f%s, %d %s)" % (
        name,
        size,
        units,
        vertex_count,
        vertex_plural,
    )


def get_recent_files(config):
    recent_files = []

    conf_files = config.read("ui.recent_files")
    if conf_files:
        for f in conf_files.split(os.path.pathsep):
            if f[-1] in ["0", "1", "2"]:
                fpath, ftype = f[:-1], OpenDialog.ftypes[int(f[-1])]
            else:
                fpath, ftype = f, None

            if os.path.exists(fpath):
                recent_files.append((os.path.basename(fpath), fpath, ftype))
        recent_files = recent_files[:RECENT_FILE_LIMIT]

    return recent_files

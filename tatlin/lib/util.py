import os
import os.path
import sys


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

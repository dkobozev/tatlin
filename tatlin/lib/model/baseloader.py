from abc import ABC, abstractmethod
import os


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

# -*- coding: utf-8 -*-
# Copyright (C) 2011 Denis Kobozev
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""
Module for loading from and writing to files.
"""
from __future__ import division

import os

from .gcodeparser import GcodeParser, GcodeParserError
from .stlparser import StlParser, StlParseError
from .actors import StlModel, GcodeModel


class ModelFileError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class ModelFile(object):
    def __init__(self, path):
        self._path = path
        self._reset_file_attributes()

        self._loaders = {
            'gcode': self._load_gcode_model,
            'stl':   self._load_stl_model,
        }

    def _reset_file_attributes(self):
        self._dirname   = None
        self._basename  = None
        self._extension = None

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
        if self.extension not in ['.gcode', '.stl']:
            raise ModelFileError('Unsupported file extension: %s' % self.extension)

        return self.extension[1:]

    def read(self, callback=None):
        return self._loaders[self.filetype](callback)

    def _load_gcode_model(self, callback=None):
        parser = GcodeParser()
        with open(self.path, 'r') as gcodefile:
            parser.load(gcodefile)
            try:
                data = parser.parse(callback)
                return GcodeModel(), data
            except GcodeParserError, e:
                # rethrow as generic file error
                raise ModelFileError("Parsing error: %s" % e.message)

    def _load_stl_model(self, callback=None):
        with open(self.path, 'rb') as stlfile:
            parser = StlParser(stlfile)
            parser.load(stlfile)
            try:
                data = parser.parse(callback)
                return StlModel(), data
            except StlParseError, e:
                # rethrow as generic file error
                raise ModelFileError("Parsing error: %s" % e.message)

    def write_stl(self, stl_model):
        assert self.filetype == 'stl'

        vertices, normals = stl_model.vertices, stl_model.normals

        f = open(self.path, 'w')
        print >>f, 'solid'
        print >>f, ''.join([self._format_facet(vertices[i:i+3], normals[i])
            for i in xrange(0, len(vertices), 3)])
        print >>f, 'endsolid'
        f.close()

    def _format_facet(self, vertices, normal):
        template = """facet normal %.6f %.6f %.6f
  outer loop
    %s
  endloop
endfacet
"""
        stl_facet = template % (normal[0], normal[1], normal[2],
            '\n'.join(['vertex %.6f %.6f %.6f' % (v[0], v[1], v[2])
                for v in vertices])
        )
        return stl_facet


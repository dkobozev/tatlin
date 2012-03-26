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
Parser for STL (stereolithography) files.
"""
import struct
import time
import logging
from cStringIO import StringIO


class StlParseError(Exception):
    pass

class InvalidTokenError(StlParseError):
    def __init__(self, line_no, msg):
        full_msg = 'parse error on line %d: %s' % (line_no, msg)
        StlParseError.__init__(self, full_msg)

class ParseEOF(StlParseError):
    pass


class StlAsciiParser(object):
    """
    Parse for ASCII STL files.

    Points of interest are:
        * create normal in _facet() method
        * create vertex in _vertex() method
        * create facet in _endfacet() method

    The rest is boring parser stuff.
    """
    def __init__(self):
        self.line_count = 0
        self.line_no = 0
        self.tokenized_peek_line = None

    def load(self, stl):
        if hasattr(stl, 'read'):
            for line in stl:
                self.line_count += 1
            stl.seek(0)
        else:
            stl = stl.split('\n')
            self.line_count = len(stl)

        self.stl = iter(stl)

    def readline(self):
        line = self.stl.next()
        if line == '':
            raise ParseEOF
        return line

    def next_line(self):
        next_line = self.peek_line()

        self.tokenized_peek_line = None # force peak line read on next call
        self.line_no += 1

        return next_line

    def peek_line(self):
        if self.tokenized_peek_line is None:
            while True:
                line = self.readline()
                self.tokenized_peek_line = self._tokenize(line)
                if len(self.tokenized_peek_line) > 0:
                    break

        return self.tokenized_peek_line

    def _tokenize(self, line):
        line = line.strip().split()
        return line

    def parse(self, callback=None):
        """
        Parse the file into a tuple of normal and facet lists.
        """
        t_start = time.time()

        self.callback = callback
        self.callback_every = self.line_count // 50 # every 2 percent
        self.callback_next = self.callback_every

        self._solid()

        if self.callback:
            self.callback(self.line_no, self.line_count)

        t_end = time.time()
        logging.info('Parsed STL ASCII file in %.2f seconds' % (t_end - t_start))

        return self.facet_list, self.normal_list

    def _solid(self):
        line = self.next_line()
        if line[0] != 'solid':
            raise InvalidTokenError(self.line_no, 'expected "%s", got "%s"' % ('solid', line[0]))

        self._facets()
        self._endsolid()

    def _endsolid(self):
        line = self.next_line()
        if line[0] != 'endsolid':
            raise InvalidTokenError(self.line_no, 'expected "%s", got "%s"' % ('endsolid', line[0]))

    def _facets(self):
        self.facet_list = []
        self.normal_list = []
        peek = self.peek_line()
        while peek[0] != 'endsolid':
            self._facet()
            peek = self.peek_line()

    def _facet(self):
        line = self.next_line()
        if line[0] != 'facet':
            raise InvalidTokenError(self.line_no, 'expected "%s", got "%s"' % ('facet', line[0]))

        if line[1] == 'normal':
            self.facet_normal = [float(line[2]), float(line[3]), float(line[4])]
        else:
            raise InvalidTokenError(self.line_no, 'expected "%s", got "%s"' % ('normal', line[1]))

        self._outer_loop()
        self._endfacet()

    def _endfacet(self):
        line = self.next_line()
        if line[0] != 'endfacet':
            raise InvalidTokenError(self.line_no, 'expected "%s", got "%s"' % ('endfacet', line[0]))

        self.facet_list.extend(self.vertex_list)
        self.normal_list.extend([self.facet_normal] * len(self.vertex_list))

        if self.callback and self.line_no >= self.callback_next:
            self.callback_next += self.callback_every
            self.callback(self.line_no, self.line_count)

    def _outer_loop(self):
        line = self.next_line()
        if ' '.join(line) != 'outer loop':
            raise InvalidTokenError(self.line_no, 'expected "%s", got "%s"' % ('outer loop', ' '.join(line)))

        self._vertices()
        self._endloop()

    def _endloop(self):
        line = self.next_line()
        if line[0] != 'endloop':
            raise InvalidTokenError(self.line_no, 'expected "%s", got "%s"' % ('endloop', line[0]))

    def _vertices(self):
        self.vertex_list = []
        peek = self.peek_line()
        while peek[0] != 'endloop':
            self._vertex()
            peek = self.peek_line()

    def _vertex(self):
        line = self.next_line()
        if line[0] != 'vertex':
            raise InvalidTokenError(self.line_no, 'expected "%s", got "%s"' % ('vertex', line[0]))
        vertex = [float(line[1]), float(line[2]), float(line[3])]
        self.vertex_list.append(vertex)


class StlBinaryParser(object):
    """
    Read data from a binary STL file.
    """
    HEADER_LEN      = 80
    FACET_COUNT_LEN = 4  # one 32-bit unsigned int
    FACET_LEN       = 50 # twelve 32-bit floats + one 16-bit short unsigned int

    def load(self, stl):
        if not hasattr(stl, 'read'):
            stl = StringIO(stl)

        self.stl = stl

    def parse(self, callback=None):
        """
        Parse the file into a tuple of normal and facet lists.
        """
        t_start = time.time()

        normal_list = []
        facet_list  = []

        self._skip_header(self.stl)
        fcount = self._facet_count(self.stl)
        callback_every = fcount // 50
        for facet_idx in xrange(fcount):
            vertices, normal = self._parse_facet(self.stl)
            facet_list.extend(vertices)
            normal_list.extend([normal] * len(vertices)) # one normal per vertex

            if callback and (facet_idx + 1) % callback_every == 0:
                callback(facet_idx + 1, fcount)

        if callback:
            callback(facet_idx + 1, fcount)

        t_end = time.time()
        logging.info('Parsed STL binary file in %.2f seconds' % (t_end - t_start))

        return facet_list, normal_list

    def _skip_header(self, fp):
        fp.seek(self.HEADER_LEN)

    def _facet_count(self, fp):
        raw = fp.read(self.FACET_COUNT_LEN)
        try:
            (count, ) = struct.unpack('<I', raw)
            return count
        except struct.error:
            raise StlParseError("Error unpacking binary STL data")

    def _parse_facet(self, fp):
        raw = fp.read(self.FACET_LEN)
        try:
            vertex_data = struct.unpack('<ffffffffffffH', raw)

            normal = [ vertex_data[0], vertex_data[1], vertex_data[2] ]
            vertices = []
            for i in range(3, 12, 3):
                vertices.append([ vertex_data[i], vertex_data[i + 1], vertex_data[i + 2] ])
            # ignore the attribute byte count...

            return vertices, normal
        except struct.error:
            raise StlParseError("Error unpacking binary STL data")


def is_stl_ascii(fp):
    """
    Guess whether file with the given name is plain ASCII STL file.
    """
    is_ascii = fp.readline().strip().startswith('solid')
    fp.seek(0)
    return is_ascii


def StlParser(fp):
    """
    STL parser that handles both ASCII and binary formats.
    """
    parser = StlAsciiParser if is_stl_ascii(fp) else StlBinaryParser
    return parser()


if __name__ == '__main__':
    import sys

    with open(sys.argv[1], 'rb') as stl:
        parser = StlParser(stl)
        parser.load(stl)
        vertices, normals = parser.parse()

        print '[ OK   ] Parsed %d vertices' % len(vertices)

        print '[ INFO ] First vertices:'
        for vertex in vertices[:3]:
            print vertex
        print '[ INFO ] First normals:'
        for normal in normals[:3]:
            print normal

        print '[ INFO ] Last vertices:'
        for vertex in vertices[-3:]:
            print vertex
        print '[ INFO ] Last normals:'
        for normal in normals[-3:]:
            print normal


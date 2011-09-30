"""
Parser for STL (stereolithography) files.
"""
from skein.vector3 import Vector3


class Facet(object):

    def __init__(self, normal, vertices):
        self.normal = normal
        self.vertices = vertices

    def __repr__(self):
        s = 'Facet(%s, %s)' % (self.normal, self.vertices)
        return s


class ParseError(Exception):
    def __init__(self, line_no, msg):
        full_msg = 'parse error on line %d: %s' % (line_no, msg)
        Exception.__init__(self, full_msg)


class ParseEOF(Exception):
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
    def __init__(self, fname):
        self.fname = fname

        self.line_no = 0
        self._line_peek = None

    def parse(self):
        """
        Return a list of facets in STL file.
        """
        self.finput = open(self.fname, 'r')
        try:
            self._solid()
        except ParseEOF:
            pass
        self.finput.close()

        return self.facet_list

    def next_line(self):
        if self._line_peek is None:
            line = self._tokenize(self.finput.readline())
        else:
            line = self._line_peek

        if len(line) == 0:
            raise ParseEOF

        self._line_peek = self._tokenize(self.finput.readline())
        self.line_no += 1

        return line

    def peek_line(self):
        return self._line_peek

    def _tokenize(self, line):
        line = line.strip().split()
        return line

    def _solid(self):
        line = self.next_line()
        if line[0] != 'solid':
            raise ParseError(self.line_no, 'expected "%s", got "%s"' % ('solid', line[0]))

        self._facets()
        self._endsolid()

    def _endsolid(self):
        line = self.next_line()
        if line[0] != 'endsolid':
            raise ParseError(self.line_no, 'expected "%s", got "%s"' % ('endsolid', line[0]))

    def _facets(self):
        self.facet_list = []
        peek = self.peek_line()
        while peek[0] != 'endsolid':
            self._facet()
            peek = self.peek_line()

    def _facet(self):
        line = self.next_line()
        if line[0] != 'facet':
            raise ParseError(self.line_no, 'expected "%s", got "%s"' % ('facet', line[0]))

        if line[1] == 'normal':
            self.facet_normal = Vector3(float(line[2]), float(line[3]), float(line[4]))
        else:
            raise ParseError(self.line_no, 'expected "%s", got "%s"' % ('normal', line[1]))

        self._outer_loop()
        self._endfacet()

    def _endfacet(self):
        line = self.next_line()
        if line[0] != 'endfacet':
            raise ParseError(self.line_no, 'expected "%s", got "%s"' % ('endfacet', line[0]))

        facet = Facet(self.facet_normal, self.vertex_list)
        self.facet_list.append(facet)

    def _outer_loop(self):
        line = self.next_line()
        if ' '.join(line) != 'outer loop':
            raise ParseError(self.line_no, 'expected "%s", got "%s"' % ('outer loop', ' '.join(line)))

        self._vertices()
        self._endloop()

    def _endloop(self):
        line = self.next_line()
        if line[0] != 'endloop':
            raise ParseError(self.line_no, 'expected "%s", got "%s"' % ('endloop', line[0]))

    def _vertices(self):
        self.vertex_list = []
        peek = self.peek_line()
        while peek[0] != 'endloop':
            self._vertex()
            peek = self.peek_line()

    def _vertex(self):
        line = self.next_line()
        if line[0] != 'vertex':
            raise ParseError(self.line_no, 'expected "%s", got "%s"' % ('vertex', line[0]))
        vertex = Vector3(float(line[1]), float(line[2]), float(line[3]))
        self.vertex_list.append(vertex)


if __name__ == '__main__':
    import sys
    parser = StlAsciiParser(sys.argv[1])
    facets = parser.parse()
    print '[ OK ] Parsed %d facets.' % len(facets)
    print 'First 5 facets:'
    for facet in facets[:5]:
        print facet


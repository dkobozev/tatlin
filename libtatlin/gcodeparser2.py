"""
Gcode parser.

Since Gcode is not standardized, this parser makes certain assumptions:

* Numeric arguments to commands are floats e.g. X95.700

"""

class GcodeParser2(object):
    def __init__(self):
        self.lines = []

    def load(self, fname):
        content = self.read_file(fname)
        self.lines = self.split_lines(content)

    def read_file(self, fname):
        f = open(fname, 'r')
        content = f.read()
        f.close()
        return content

    def split_lines(self, content):
        lines = content.replace('\r', '\n').replace('\n\n', '\n').split('\n')
        return lines

    def parse(self):
        parsed = [self.parse_line(line) for line in self.lines]
        return parsed

    def parse_line(self, line):
        command, comment = self.split_comment(line)
        parts = command.split()
        if parts:
            return (parts[0], self.parse_args(parts[1:]), comment)
        else:
            return ('', {}, comment)

    def split_comment(self, line):
        idx_semi = line.find(';')
        if idx_semi >= 0:
            command, comment = line[:idx_semi], line[idx_semi:]
        else:
            command, comment = line, ''

        idx_paren = command.find('(')
        if idx_paren >= 0:
            command, comment = (command[:idx_paren],
                                command[idx_paren:] + comment)

        return (command, comment)

    def parse_args(self, args):
        d = {}
        for arg in args:
            d[arg[0]] = float(arg[1:])
        return d


if __name__ == '__main__':
    import sys
    p = GcodeParser2()
    p.load(sys.argv[1])
    p.parse()

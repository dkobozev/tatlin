"""
Gcode parser.

Since Gcode is not standardized, this parser makes certain assumptions:

* Numeric arguments to commands are floats e.g. X95.700

"""

class GcodeParserError(Exception):
    pass

class GcodeArgumentError(GcodeParserError):
    pass


class GcodeLexer(object):
    """
    Load gcode and split commands into tokens.
    """
    def __init__(self):
        self.lines = []
        self.line_no = None
        self.current_line = None

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

    def scan(self):
        try:
            all_tokens = []
            for line_idx, line in enumerate(self.lines):
                self.line_no = line_idx + 1
                self.current_line = line
                tokens = self.scan_line(line)
                all_tokens.append(tokens)

            return all_tokens
        except GcodeArgumentError as e:
            raise GcodeParserError('Error parsing arguments: %s on line %d\n'
                '\t%s' % (str(e), self.line_no, self.current_line))

    def scan_line(self, line):
        command, comment = self.split_comment(line)
        parts = command.split()
        if parts:
            return (parts[0], self.scan_args(parts[1:]), comment)
        else:
            return ('', {}, comment)

    def split_comment(self, line):
        """
        Comments start with a semicolon ; or a open parentheses (.
        """
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

    def scan_args(self, args):
        d = {}
        for arg in args:
            try:
                # argument consists of an axis name and an optional number
                if arg[1:]:
                    d[arg[0]] = float(arg[1:])
                else:
                    d[arg[0]] = None
            except ValueError as e:
                raise GcodeArgumentError(str(e))
        return d


class Movement(object):
    """
    Movement represents travel between two points and machine state during
    travel.
    """
    FLAG_PERIMETER       = 1
    FLAG_PERIMETER_OUTER = 2
    FLAG_LOOP            = 4
    FLAG_SURROUND_LOOP   = 8

    def __init__(self, src, dst, delta_e, feedrate, flags=0):
        self.src = src
        self.dst   = dst

        self.delta_e  = delta_e
        self.feedrate = feedrate
        self.flags    = flags


class GcodeParser(object):

    marker_layer                  = '(<layer>'
    marker_perimeter_start        = '(<perimeter>'
    marker_perimeter_end          = '(</perimeter>)'
    marker_loop_start             = '(<loop>'
    marker_loop_end               = '(</loop>)'
    marker_surrounding_loop_start = '(<surroundingLoop>)'
    marker_surrounding_loop_end   = '(</surroundingLoop>)'

    def __init__(self):
        self.fname = None
        self.lexer = GcodeLexer()
        self.prev_coords = None
        self.e_len = 0
        self.flags = 0

    def load(self, fname):
        self.fname = fname
        self.lexer.load(fname)

    def parse(self):
        layers = []
        movements = []

        commands_gen = self.lexer.scan()
        first_command = commands_gen.next()
        self.prev_coords = self.command_coords(first_command[1])
        self.read_command_state(first_command)

        for command in commands_gen:
            # create new movement
            dst = self.command_coords(command)
            e_len = command[1]['E']
            delta_e = e_len - self.e_len
            feedrate = command[1]['F']

            movement = Movement(self.prev_coords, dst, delta_e, feedrate,
                                self.flags)
            movements.append(movement)

            # update parser state
            self.prev_coords = dst
            self.read_command_state(command)
            self.e_len = e_len

            movements.append(movement)

            if self.is_new_layer():
                layers.append(movements)
                movements = []

        if len(movements) > 0:
            layers.append(movements)

        return layers

    def read_command_state(self, command):
        """
        Set internal parser state based on command arguments.
        """
        gcode, args, comment = command

        if self.marker_loop_start in comment:
            self.flags |= Movement.FLAG_LOOP

        elif self.marker_loop_end in comment:
            self.flags &= ~Movement.FLAG_LOOP

        elif self.marker_perimeter_start in comment:
            self.flags |= Movement.FLAG_PERIMETER
            if 'outer' in comment:
                self.flags |= Movement.FLAG_PERIMETER_OUTER

        elif self.marker_perimeter_end in comment:
            self.flags &= ~(Movement.FLAG_PERIMETER |
                            Movement.FLAG_PERIMETER_OUTER)

        elif self.marker_surrounding_loop_start in comment:
            self.flags |= Movement.FLAG_SURROUND_LOOP

        elif self.marker_surrounding_loop_end in comment:
            self.flags &= ~Movement.FLAG_SURROUND_LOOP

    def command_coords(self, args):
        coords = (args['X'], args['Y'], args['Z'])
        return coords


if __name__ == '__main__':
    import sys
    p = GcodeLexer()
    p.load(sys.argv[1])
    p.scan()

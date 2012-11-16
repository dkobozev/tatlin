# -*- coding: utf-8 -*-
# Copyright (C) 2012 Denis Kobozev
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
Gcode parser.
"""

from __future__ import division

import time
import logging
import math


class GcodeParserError(Exception):
    pass

class GcodeArgumentError(GcodeParserError):
    pass


class ArgsDict(dict):
    """
    Dictionary that returns None on missing keys instead of throwing a
    KeyError.
    """
    def __missing__(self, key):
        return None


class GcodeLexer(object):
    """
    Load gcode and split commands into tokens.
    """
    def __init__(self):
        self.lines = []
        self.line_no = None
        self.current_line = None
        self.line_count = 0

    def load(self, gcode):
        content = self.read_input(gcode)
        self.lines = self.split_lines(content)
        self.line_count = len(self.lines)

    def read_input(self, src):
        """
        Accept string or a file-like object to read input from.
        """
        if hasattr(src, 'read'):
            content = src.read()
        else:
            content = src
        return content

    def split_lines(self, content):
        """
        Break input into lines.
        """
        lines = content.replace('\r', '\n').replace('\n\n', '\n').split('\n')
        return lines

    def scan(self):
        """
        Return a generator for commands split into tokens.
        """
        try:
            for line_idx, line in enumerate(self.lines):
                self.line_no = line_idx + 1
                self.current_line = line
                tokens = self.scan_line(line)

                if not self.is_blank(tokens):
                    yield tokens
        except GcodeArgumentError as e:
            error_msg = str(e).strip()
            if error_msg.endswith(':'):
                error_msg = error_msg[:-1]

            raise GcodeParserError('Error parsing arguments: %s on line %d\n' % (
                error_msg, self.line_no))

    def scan_line(self, line):
        """
        Break line into tokens.
        """
        command, comment = self.split_comment(line)
        parts = command.split()
        if parts:
            return (parts[0], self.scan_args(parts[1:]), comment)
        else:
            return ('', ArgsDict(), comment)

    def split_comment(self, line):
        """
        Return a 2-tuple of command and comment.

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
        """
        Build a map of axis names to axis values.
        """
        d = ArgsDict()
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

    def is_blank(self, tokens):
        """
        Return true if tokens does not contain any information.
        """
        return tokens == ('', ArgsDict(), '')


class Movement(object):
    """
    Movement represents travel between two points and machine state during
    travel.
    """
    FLAG_PERIMETER       = 1
    FLAG_PERIMETER_OUTER = 2
    FLAG_LOOP            = 4
    FLAG_SURROUND_LOOP   = 8
    FLAG_EXTRUDER_ON     = 16

    def __init__(self, src, dst, delta_e, feedrate, flags=0):
        self.src = src
        self.dst = dst

        self.delta_e  = delta_e
        self.feedrate = feedrate
        self.flags    = flags

    def angle(self, precision=0):
        x = self.dst[0] - self.src[0]
        y = self.dst[1] - self.src[1]
        angle = math.degrees(math.atan2(y, -x)) # negate x for clockwise rotation angle
        return round(angle, precision)

    def __str__(self):
        s = "(%s => %s)" % (self.src, self.dst)
        return s

    def __repr__(self):
        s = "Movement(%s, %s, %s, %s, %s)" % (
            self.src, self.dst, self.delta_e, self.feedrate, self.flags
        )
        return s


class GcodeParser(object):

    marker_layer                  = '(<layer>'
    marker_perimeter_start        = '(<perimeter>'
    marker_perimeter_end          = '(</perimeter>)'
    marker_loop_start             = '(<loop>'
    marker_loop_end               = '(</loop>)'
    marker_surrounding_loop_start = '(<surroundingLoop>)'
    marker_surrounding_loop_end   = '(</surroundingLoop>)'

    def __init__(self):
        self.lexer = GcodeLexer()

        self.src       = (None, )
        self.e_len     = 0
        self.flags     = 0
        self.prev_args = ArgsDict()
        self.set_flags = self.set_flags_skeinforge

    def load(self, src):
        self.lexer.load(src)

    def parse(self, callback=None):
        t_start = time.time()

        layers = []
        movements = []
        line_count = self.lexer.line_count
        callback_every = round(line_count / 50)

        for command_idx, command in enumerate(self.lexer.scan()):
            gcode, newargs, comment = command

            if 'Slic3r' in comment:
                # switch mode to slic3r
                self.set_flags = self.set_flags_slic3r

            args = self.update_args(newargs)
            dst  = self.command_coords(gcode, args)

            e_len, delta_e = self.process_e_axis(gcode, args)
            feedrate = args['F']
            self.set_flags(command)

            if None not in self.src and None not in dst and self.src != dst:
                move = Movement(self.src, dst, delta_e, feedrate, self.flags)
                movements.append(move)

                if self.is_new_layer(dst, gcode, comment):
                    layers.append(movements)
                    movements = []

            if None not in dst:
                self.src = dst
            self.prev_args = args
            self.e_len = e_len

            if callback and command_idx % callback_every == 0:
                callback(command_idx + 1, line_count)

        # don't forget leftover movements
        if len(movements) > 0:
            layers.append(movements)

        if callback:
            callback(command_idx + 1, line_count)

        t_end = time.time()
        logging.info('Parsed Gcode file in %.2f seconds' % (t_end - t_start))

        if len(layers) < 1:
            raise GcodeParserError("File does not contain valid Gcode")

        logging.info('Layers: %d' % len(layers))

        return layers

    def update_args(self, args):
        prev_args = self.prev_args.copy()
        prev_args.update(args)
        return ArgsDict(prev_args)

    def set_flags_skeinforge(self, command):
        """
        Set internal parser state based on command arguments assuming the file
        has been generated by Skeinforge.
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

        elif gcode == 'M101': # turn on extruder
            self.flags |= Movement.FLAG_EXTRUDER_ON

        elif gcode == 'M103': # turn off extruder
            self.flags &= ~Movement.FLAG_EXTRUDER_ON

    def set_flags_slic3r(self, command):
        """
        Set internal parser state based on command arguments assuming the file
        has been generated by Slic3r.
        """
        gcode, args, comment = command

        if 'perimeter' in comment:
            self.flags |= (Movement.FLAG_PERIMETER |
                           Movement.FLAG_PERIMETER_OUTER)
        elif 'skirt' in comment:
            self.flags |= Movement.FLAG_LOOP
        else:
            self.flags = 0

    def command_coords(self, gcode, args):
        if gcode == 'G1' or gcode == 'G01':
            coords = (args['X'], args['Y'], args['Z'])
            return coords
        return (None, )

    def is_new_layer(self, dst, gcode, comment):
        if self.marker_layer in comment:
            return True

        if gcode in ('G1', 'G01', 'G2', 'G02', 'G3', 'G03'):
            delta_z = dst[2] - self.src[2]
            if delta_z > 0.1:
                return True

        return False

    def process_e_axis(self, gcode, args):
        e_len = args['E']
        if gcode == 'G92' and e_len == 0:
            # reset the extruder
            self.e_len = None
            delta_e = 0
        elif self.e_len is None or e_len is None:
            delta_e = 0
        else:
            delta_e = e_len - self.e_len

        return (e_len, delta_e)


if __name__ == '__main__':
    import sys
    p = GcodeLexer()
    with open(sys.argv[1], 'r') as f:
        p.load(f)
    p.scan()

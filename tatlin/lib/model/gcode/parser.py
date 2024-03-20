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


import time
import logging
import math
import array


class GcodeParserError(Exception):
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
        self.line_no = None
        self.current_line = None
        self.line_count = 0

    def load(self, gcode):
        if isinstance(gcode, str):
            lines = gcode.replace("\r", "\n").replace("\n\n", "\n").split("\n")
            self.line_count = len(lines)

            def _getlines():  # type: ignore
                for line in lines:
                    yield line

            self.getlines = _getlines
        else:
            for line in gcode:
                self.line_count += 1

            gcode.seek(0)

            def _getlines():
                for line in gcode:
                    yield line.replace("\r", "\n").replace("\n\n", "\n")

            self.getlines = _getlines

    def scan(self):
        """
        Return a generator for commands split into tokens.
        """
        self.line_no = 0
        for line in self.getlines():
            self.line_no += 1
            self.current_line = line
            tokens = self.scan_line(line)

            if not self.is_blank(tokens):
                yield tokens

    def scan_line(self, line):
        """
        Break line into tokens.
        """
        command, comment = self.split_comment(line)
        parts = command.split()
        if parts:
            args = ArgsDict()
            for part in reversed(parts[1:]):
                if len(part) > 1:
                    try:
                        args[part[0]] = float(part[1:])
                    except ValueError as e:
                        comment = part + " " + comment
                else:
                    args[part[0]] = None

            return (parts[0], args, comment)
        else:
            return ("", ArgsDict(), comment)

    def split_comment(self, line):
        """
        Return a 2-tuple of command and comment.

        Comments start with a semicolon ; or a open parentheses (.
        """
        idx_semi = line.find(";")
        if idx_semi >= 0:
            command, comment = line[:idx_semi], line[idx_semi:]
        else:
            command, comment = line, ""

        idx_paren = command.find("(")
        if idx_paren >= 0:
            command, comment = (command[:idx_paren], command[idx_paren:] + comment)

        return (command, comment)

    def is_blank(self, tokens):
        """
        Return true if tokens does not contain any information.
        """
        return tokens == ("", ArgsDict(), "")


class Movement(object):
    """
    Movement represents travel between two points and machine state during
    travel.
    """

    FLAG_PERIMETER = 1
    FLAG_PERIMETER_OUTER = 2
    FLAG_LOOP = 4
    FLAG_SURROUND_LOOP = 8
    FLAG_EXTRUDER_ON = 16
    FLAG_INCHES = 32

    # tell the python interpreter to only allocate memory for the following attributes
    __slots__ = ["v", "delta_e", "feedrate", "flags"]

    def __init__(self, v, delta_e, feedrate, flags=0):
        self.v = v

        self.delta_e = delta_e
        self.feedrate = feedrate
        self.flags = flags

    def angle(self, start, precision=0):
        x = self.v[0] - start[0]
        y = self.v[1] - start[1]
        angle = math.degrees(math.atan2(y, -x))  # negate x for clockwise rotation angle
        return round(angle, precision)

    def __str__(self):
        s = "(%s)" % (self.v)
        return s

    def __repr__(self):
        s = "Movement(%s, %s, %s, %s)" % (
            self.v,
            self.delta_e,
            self.feedrate,
            self.flags,
        )
        return s


class GcodeParser(object):
    marker_layer = "</layer>"
    marker_perimeter_start = "<perimeter>"
    marker_perimeter_end = "</perimeter>)"
    marker_loop_start = "<loop>"
    marker_loop_end = "</loop>"
    marker_surrounding_loop_start = "<surroundingLoop>"
    marker_surrounding_loop_end = "</surroundingLoop>"

    def __init__(self):
        self.lexer = GcodeLexer()

        self.args = ArgsDict({"X": 0, "Y": 0, "Z": 0, "F": 0, "E": 0})
        self.offset = {"X": 0, "Y": 0, "Z": 0, "E": 0}
        self.src = None
        self.flags = 0
        self.set_flags = self.set_flags_skeinforge
        self.relative = False

    def load(self, src):
        self.lexer.load(src)

    def parse(self, callback=None):
        t_start = time.time()

        layers = []
        movements = []
        line_count = self.lexer.line_count
        command_idx = None
        callback_every = max(1, int(math.floor(line_count / 100)))
        mm_in_inch = 25.4
        new_layer = False
        current_layer_z = 0

        for command_idx, command in enumerate(self.lexer.scan()):
            gcode, newargs, comment = command

            if "Slic3r" in comment:
                # switch mode to slic3r
                self.set_flags = self.set_flags_slic3r

            args = self.update_args(self.args, newargs)
            dst = self.command_coords(gcode, args, newargs)
            delta_e = args["E"] - self.args["E"]
            self.set_flags(command)

            if self.marker_layer in comment:
                new_layer = True
            if delta_e > 0 and args["Z"] != current_layer_z:
                current_layer_z = args["Z"]
                new_layer = True

            # create a new movement if the gcode contains a valid coordinate
            if dst is not None and self.src != dst:
                if self.src is not None and new_layer:
                    layers.append(movements)
                    movements = []
                    new_layer = False

                if self.flags & Movement.FLAG_INCHES:
                    dst = (
                        dst[0] * mm_in_inch,
                        dst[1] * mm_in_inch,
                        dst[2] * mm_in_inch,
                    )

                move = Movement(array.array("f", dst), delta_e, args["F"], self.flags)
                movements.append(move)

            # if gcode contains a valid coordinate, update the previous point
            # with the new coordinate
            if dst is not None:
                self.src = dst
            self.args = args

            if callback and command_idx % callback_every == 0:
                callback(command_idx + 1, line_count)

        # don't forget leftover movements
        if len(movements) > 0:
            layers.append(movements)

        if callback and command_idx is not None:
            callback(command_idx + 1, line_count)

        t_end = time.time()
        logging.info("Parsed Gcode file in %.2f seconds" % (t_end - t_start))

        if len(layers) < 1:
            raise GcodeParserError("File does not contain valid Gcode")

        logging.info("Layers: %d" % len(layers))

        return layers

    def update_args(self, oldargs, newargs):
        args = oldargs.copy()

        for axis in list(newargs.keys()):
            if axis in args and newargs[axis] is not None:
                if self.relative:
                    args[axis] += newargs[axis]
                else:
                    args[axis] = newargs[axis]

        return args

    def command_coords(self, gcode, args, newargs):
        if gcode in ("G0", "G00", "G1", "G01"):  # move
            coords = (
                self.offset["X"] + args["X"],
                self.offset["Y"] + args["Y"],
                self.offset["Z"] + args["Z"],
            )
            return coords
        elif gcode == "G28":  # move to origin
            if newargs["X"] is None and newargs["Y"] is None and newargs["Z"] is None:
                # if no coordinates specified, move all axes to origin
                return (self.offset["X"], self.offset["Y"], self.offset["Z"])
            else:
                # if any coordinates are specified, reset just the axes
                # specified; the actual coordinate values are ignored
                x = self.offset["X"] if newargs["X"] is not None else args["X"]
                y = self.offset["Y"] if newargs["Y"] is not None else args["Y"]
                z = self.offset["Z"] if newargs["Z"] is not None else args["Z"]
                return (x, y, z)
        elif gcode == "G90":  # set to absolute positioning
            self.relative = False
        elif gcode == "G91":  # set to relative positioning
            self.relative = True
        elif gcode == "G92":  # set position
            # G92 without coordinates resets all axes to zero
            if len(newargs) < 1:
                newargs = ArgsDict({"X": 0, "Y": 0, "Z": 0, "E": 0})

            for axis in list(newargs.keys()):
                if axis in self.offset:
                    self.offset[axis] += self.args[axis] - newargs[axis]
                    self.args[axis] = newargs[axis]

        return None

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
            if "outer" in comment:
                self.flags |= Movement.FLAG_PERIMETER_OUTER

        elif self.marker_perimeter_end in comment:
            self.flags &= ~(Movement.FLAG_PERIMETER | Movement.FLAG_PERIMETER_OUTER)

        elif self.marker_surrounding_loop_start in comment:
            self.flags |= Movement.FLAG_SURROUND_LOOP

        elif self.marker_surrounding_loop_end in comment:
            self.flags &= ~Movement.FLAG_SURROUND_LOOP

        elif gcode in ("M101", "M3", "M03", "M4", "M04"):  # turn on extruder/spindle
            self.flags |= Movement.FLAG_EXTRUDER_ON

        elif gcode in ("M103", "M5", "M05"):  # turn off extruder/spindle
            self.flags &= ~Movement.FLAG_EXTRUDER_ON

        elif gcode == "G20":
            self.flags |= Movement.FLAG_INCHES

        elif gcode == "G21":
            self.flags &= ~Movement.FLAG_INCHES

    def set_flags_slic3r(self, command):
        """
        Set internal parser state based on command arguments assuming the file
        has been generated by Slic3r.
        """
        gcode, args, comment = command

        if "perimeter" in comment:
            self.flags |= Movement.FLAG_PERIMETER | Movement.FLAG_PERIMETER_OUTER
        elif "skirt" in comment:
            self.flags |= Movement.FLAG_LOOP
        else:
            self.flags = 0

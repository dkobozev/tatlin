from __future__ import division

import math
import time
import logging

from . import gcodec
from .vector3 import Vector3


class Movement(object):
    def __init__(self, point_a, point_b, extruder_on=False, is_perimeter=False,
            is_loop=False, is_perimeter_outer=False, is_surrounding_loop=False):
        self.point_a = point_a
        self.point_b = point_b
        self.extruder_on = extruder_on
        self.is_perimeter = is_perimeter
        self.is_loop = is_loop
        self.is_perimeter_outer = is_perimeter_outer
        self.is_surrounding_loop = is_surrounding_loop

    def points(self):
        return (self.point_a, self.point_b)

    def angle(self):
        x = self.point_b.x - self.point_a.x
        y = self.point_b.y - self.point_a.y
        angle = math.degrees(math.atan2(y, -x)) # negate x for clockwise rotation angle
        return angle


class GcodeParser(object):

    marker_layer                  = '(<layer>'
    marker_perimeter_start        = '(<perimeter>'
    marker_perimeter_end          = '(</perimeter>)'
    marker_loop_start             = '(<loop>'
    marker_loop_end               = '(</loop>)'
    marker_surrounding_loop_start = '(<surroundingLoop>)'
    marker_surrounding_loop_end   = '(</surroundingLoop>)'

    def __init__(self, fname, start_location=None):
        self.fname = fname
        self.gcode_lines = self.split(self.read())

        self.is_new_layer = self.is_new_layer_from_marker if self.file_has_layer_markers() else self.is_new_layer_from_gcode

        if start_location is None:
            start_location = Vector3(0.0, 0.0, 0.0)
        self.prev_location = start_location

        self.extruder_on         = False
        self.is_perimeter        = False
        self.is_perimeter_outer  = False
        self.is_loop             = False
        self.is_surrounding_loop = False

    def split(self, s):
        lines = s.replace('\r', '\n').replace('\n\n', '\n').split('\n')
        return lines

    def read(self):
        f = open(self.fname, 'r')
        content = f.read()
        f.close()
        return content

    def parse(self):
        t_start = time.time()

        layers = []
        layer = []
        for line in self.gcode_lines:
            split_line = gcodec.getSplitLineBeforeBracketSemicolon(line)

            if len(split_line) < 1:
                continue

            if self.is_new_layer(split_line): # start new layer if necessary
                layers.append(layer)
                layer = []

            location = self.parse_location(split_line)
            if location != self.prev_location:
                movement = Movement(point_a=self.prev_location, point_b=location,
                    extruder_on=self.extruder_on,
                    is_perimeter=self.is_perimeter,
                    is_perimeter_outer=self.is_perimeter_outer,
                    is_loop=self.is_loop,
                    is_surrounding_loop=self.is_surrounding_loop
                )
                layer.append(movement)
                self.prev_location = location

        layers.append(layer)

        t_end = time.time()
        logging.info('Parsed Gcode file in %.2f seconds' % (t_end - t_start))

        return layers

    def parse_location(self, split_line):
        first_word = split_line[0]
        location = self.prev_location
        if first_word == 'G1': # linear travel
            location = gcodec.getLocationFromSplitLine(self.prev_location, split_line)
        elif first_word == 'M101': # turn extruder forward
            self.extruder_on = True
        elif first_word == 'M103': # turn extruder off
            self.extruder_on = False
            self.is_loop = False
            self.is_perimeter = False
        elif first_word == self.marker_loop_start:
            self.is_loop = True
        elif first_word == self.marker_loop_end:
            self.is_loop = False
        elif first_word == self.marker_perimeter_start:
            self.is_perimeter = True
            self.is_perimeter_outer = (split_line[1] == 'outer')
        elif first_word == self.marker_perimeter_end:
            self.is_perimeter = False
        elif first_word == self.marker_surrounding_loop_start:
            self.is_surrounding_loop = True
        elif first_word == self.marker_surrounding_loop_end:
            self.is_surrounding_loop = False

        return location

    def file_has_layer_markers(self):
        has_markers = gcodec.isThereAFirstWord(self.marker_layer, self.gcode_lines, 1)
        return has_markers

    def is_new_layer_from_marker(self, split_line):
        return split_line[0] == self.marker_layer

    def is_new_layer_from_gcode(self, split_line):
        is_new_layer = False

        if split_line[0] in ('G1', 'G2', 'G3'):
            new_location = gcodec.getLocationFromSplitLine(self.prev_location, split_line)
            if new_location.z - self.prev_location.z > 0.1:
                is_new_layer = True

        return is_new_layer


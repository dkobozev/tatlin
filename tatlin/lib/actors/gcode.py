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


import math
import numpy
import logging
import time

from OpenGL.GL import *  # type:ignore
from OpenGL.GLE import *  # type:ignore
from OpenGL.arrays.vbo import VBO

from .model import Model

from tatlin.lib import vector
from tatlin.lib.parsers.gcode.parser import Movement


class GcodeModel(Model):
    """
    Model for displaying Gcode data.
    """

    # vertices for arrow to display the direction of movement
    arrow = numpy.require(
        [
            [0.0, 0.0, 0.0],
            [0.4, -0.1, 0.0],
            [0.4, 0.1, 0.0],
        ],
        "f",
    )
    layer_entry_marker = numpy.require(
        [
            [0.23, -0.14, 0.0],
            [0.0, 0.26, 0.0],
            [-0.23, -0.14, 0.0],
        ],
        "f",
    )
    layer_exit_marker = numpy.require(
        [
            [-0.23, -0.23, 0.0],
            [0.23, -0.23, 0.0],
            [0.23, 0.23, 0.0],
            [0.23, 0.23, 0.0],
            [-0.23, 0.23, 0.0],
            [-0.23, -0.23, 0.0],
        ],
        "f",
    )

    def load_data(self, model_data, callback=None):
        t_start = time.time()

        vertex_list = []
        color_list = []
        self.layer_stops = [0]
        self.layer_heights = []
        arrow_list = []
        layer_markers_list = []
        self.layer_marker_stops = [0]

        num_layers = len(model_data)
        callback_every = max(1, int(math.floor(num_layers / 100)))

        # the first movement designates the starting point
        start = prev = model_data[0][0]
        del model_data[0][0]
        for layer_idx, layer in enumerate(model_data):
            first = layer[0]
            for movement in layer:
                vertex_list.append(prev.v)
                vertex_list.append(movement.v)
                arrow = self.arrow
                # position the arrow with respect to movement
                arrow = vector.rotate(arrow, movement.angle(prev.v), 0.0, 0.0, 1.0)
                arrow_list.extend(arrow)
                vertex_color = self.movement_color(movement)
                color_list.append(vertex_color)
                prev = movement

            self.layer_stops.append(len(vertex_list))
            self.layer_heights.append(first.v[2])

            # add the layer entry marker
            if layer_idx > 0 and len(model_data[layer_idx - 1]) > 0:
                layer_markers_list.extend(
                    self.layer_entry_marker + model_data[layer_idx - 1][-1].v
                )
            elif layer_idx == 0 and len(layer) > 0:
                layer_markers_list.extend(self.layer_entry_marker + layer[0].v)

            # add the layer exit marker
            if len(layer) > 1:
                layer_markers_list.extend(self.layer_exit_marker + layer[-1].v)

            self.layer_marker_stops.append(len(layer_markers_list))

            if callback and layer_idx % callback_every == 0:
                callback(layer_idx + 1, num_layers)

        self.vertices = numpy.array(vertex_list, "f")
        self.colors = numpy.array(color_list, "f")
        self.arrows = numpy.array(arrow_list, "f")
        self.layer_markers = numpy.array(layer_markers_list, "f")

        # by translating the arrow vertices outside of the loop, we achieve a
        # significant performance gain thanks to numpy. it would be really nice
        # if we could rotate in a similar fashion...
        self.arrows = self.arrows + self.vertices[1::2].repeat(3, 0)

        # for every pair of vertices of the model, there are 3 vertices for the arrow
        assert len(self.arrows) == (
            (len(self.vertices) // 2) * 3
        ), "The 2:3 ratio of model vertices to arrow vertices does not hold."

        self.max_layers = len(self.layer_stops) - 1
        self.num_layers_to_draw = self.max_layers
        self.arrows_enabled = True
        self.initialized = False
        self.vertex_count = len(self.vertices)

        t_end = time.time()

        logging.info("Initialized Gcode model in %.2f seconds" % (t_end - t_start))
        logging.info("Vertex count: %d" % self.vertex_count)

    def movement_color(self, move):
        """
        Return the color to use for particular type of movement.
        """
        # default movement color is gray
        color = (0.6, 0.6, 0.6, 0.6)

        extruder_on = move.flags & Movement.FLAG_EXTRUDER_ON or move.delta_e > 0
        outer_perimeter = (
            move.flags & Movement.FLAG_PERIMETER
            and move.flags & Movement.FLAG_PERIMETER_OUTER
        )

        if extruder_on and outer_perimeter:
            color = (0.0, 0.875, 0.875, 0.6)  # cyan
        elif extruder_on and move.flags & Movement.FLAG_PERIMETER:
            color = (0.0, 1.0, 0.0, 0.6)  # green
        elif extruder_on and move.flags & Movement.FLAG_LOOP:
            color = (1.0, 0.875, 0.0, 0.6)  # yellow
        elif extruder_on:
            color = (1.0, 0.0, 0.0, 0.6)  # red

        return color

    # ------------------------------------------------------------------------
    # DRAWING
    # ------------------------------------------------------------------------

    def init(self):
        self.vertex_buffer = VBO(self.vertices, "GL_STATIC_DRAW")
        self.vertex_color_buffer = VBO(
            self.colors.repeat(2, 0), "GL_STATIC_DRAW"
        )  # each pair of vertices shares the color

        if self.arrows_enabled:
            self.arrow_buffer = VBO(self.arrows, "GL_STATIC_DRAW")
            self.arrow_color_buffer = VBO(
                self.colors.repeat(3, 0), "GL_STATIC_DRAW"
            )  # each triplet of vertices shares the color

        self.layer_marker_buffer = VBO(self.layer_markers, "GL_STATIC_DRAW")

        self.initialized = True

    def display(self, elevation=0, eye_height=0, mode_ortho=False, mode_2d=False):
        glPushMatrix()

        offset_z = self.offset_z if not mode_2d else 0
        glTranslate(self.offset_x, self.offset_y, offset_z)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        self._display_movements(elevation, eye_height, mode_ortho, mode_2d)

        if self.arrows_enabled:
            self._display_arrows()

        glDisableClientState(GL_COLOR_ARRAY)

        if self.arrows_enabled:
            self._display_layer_markers()

        glDisableClientState(GL_VERTEX_ARRAY)
        glPopMatrix()

    def _display_movements(
        self, elevation=0, eye_height=0, mode_ortho=False, mode_2d=False
    ):
        self.vertex_buffer.bind()
        glVertexPointer(3, GL_FLOAT, 0, None)

        self.vertex_color_buffer.bind()
        glColorPointer(4, GL_FLOAT, 0, None)

        if mode_2d:
            glScale(1.0, 1.0, 0.0)  # discard z coordinates
            start = self.layer_stops[self.num_layers_to_draw - 1]
            end = self.layer_stops[self.num_layers_to_draw]
            glDrawArrays(GL_LINES, start, end - start)

        elif mode_ortho:
            if elevation >= 0:
                # draw layers in normal order, bottom to top
                start = 0
                end = self.layer_stops[self.num_layers_to_draw]
                glDrawArrays(GL_LINES, start, end - start)

            else:
                # draw layers in reverse order, top to bottom
                stop_idx = self.num_layers_to_draw - 1
                while stop_idx >= 0:
                    start = self.layer_stops[stop_idx]
                    end = self.layer_stops[stop_idx + 1]
                    glDrawArrays(GL_LINES, start, end - start)
                    stop_idx -= 1

        else:  # 3d projection mode
            reverse_threshold_layer = self._layer_up_to_height(
                eye_height - self.offset_z
            )

            if reverse_threshold_layer >= 0:
                # draw layers up to (and including) the threshold in normal order, bottom to top
                normal_layers_to_draw = min(
                    self.num_layers_to_draw, reverse_threshold_layer + 1
                )
                start = 0
                end = self.layer_stops[normal_layers_to_draw]
                glDrawArrays(GL_LINES, start, end - start)

            if reverse_threshold_layer + 1 < self.num_layers_to_draw:
                # draw layers from the threshold in reverse order, top to bottom
                stop_idx = self.num_layers_to_draw - 1
                while stop_idx > reverse_threshold_layer:
                    start = self.layer_stops[stop_idx]
                    end = self.layer_stops[stop_idx + 1]
                    glDrawArrays(GL_LINES, start, end - start)
                    stop_idx -= 1

        self.vertex_buffer.unbind()
        self.vertex_color_buffer.unbind()

    def _layer_up_to_height(self, height):
        """Return the index of the last layer lower than height."""
        for idx in range(len(self.layer_heights) - 1, -1, -1):
            if self.layer_heights[idx] < height:
                return idx

        return 0

    def _display_arrows(self):
        self.arrow_buffer.bind()
        glVertexPointer(3, GL_FLOAT, 0, None)

        self.arrow_color_buffer.bind()
        glColorPointer(4, GL_FLOAT, 0, None)

        start = (self.layer_stops[self.num_layers_to_draw - 1] // 2) * 3
        end = (self.layer_stops[self.num_layers_to_draw] // 2) * 3

        glDrawArrays(GL_TRIANGLES, start, end - start)

        self.arrow_buffer.unbind()
        self.arrow_color_buffer.unbind()

    def _display_layer_markers(self):
        self.layer_marker_buffer.bind()
        glVertexPointer(3, GL_FLOAT, 0, None)

        start = self.layer_marker_stops[self.num_layers_to_draw - 1]
        end = self.layer_marker_stops[self.num_layers_to_draw]

        glColor4f(0.6, 0.6, 0.6, 0.6)
        glDrawArrays(GL_TRIANGLES, start, end - start)

        self.layer_marker_buffer.unbind()

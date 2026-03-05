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
from tatlin.lib.model.gcode.parser import Movement


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
        normal_list = []
        color_list = []
        self.layer_stops = [0]
        self.layer_heights = []
        arrow_list = []
        arrow_endpoints = []  # Track movement endpoints for arrow positioning
        layer_markers_list = []
        self.layer_marker_stops = [0]

        # Track line numbers for each movement (for highlighting selected lines)
        self.movement_line_numbers = []  # List of line numbers, one per movement
        self.selected_lines = set()  # Set of selected line numbers

        num_layers = len(model_data)
        callback_every = max(1, int(math.floor(num_layers / 100)))

        # cylinder parameters
        cylinder_sides = 8
        cylinder_radius = 0.1  # thin cylinder radius in mm

        # the first movement designates the starting point
        start = prev = model_data[0][0]
        del model_data[0][0]
        for layer_idx, layer in enumerate(model_data):
            first = layer[0]
            for movement in layer:
                # Generate cylinder geometry for this movement segment
                vertices, normals = self._generate_cylinder(
                    prev.v, movement.v, cylinder_radius, cylinder_sides
                )
                vertex_list.extend(vertices)
                normal_list.extend(normals)

                arrow = self.arrow
                # position the arrow with respect to movement
                arrow = vector.rotate(arrow, movement.angle(prev.v), 0.0, 0.0, 1.0)
                arrow_list.extend(arrow)
                arrow_endpoints.append(movement.v)  # Store the actual movement endpoint

                # Track line number for this movement
                self.movement_line_numbers.append(movement.line_no)

                vertex_color = self.movement_color(movement)
                # Each cylinder has cylinder_sides * 6 vertices (2 triangles per side, 3 vertices per triangle)
                num_cylinder_vertices = cylinder_sides * 6
                for _ in range(num_cylinder_vertices):
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
        self.normals = numpy.array(normal_list, "f")
        self.colors = numpy.array(color_list, "f")
        self.arrows = numpy.array(arrow_list, "f")
        self.layer_markers = numpy.array(layer_markers_list, "f")

        # Position arrows at movement endpoints
        # by translating the arrow vertices outside of the loop, we achieve a
        # significant performance gain thanks to numpy
        if len(arrow_endpoints) > 0:
            arrow_endpoints_array = numpy.array(arrow_endpoints, "f")
            self.arrows = self.arrows + arrow_endpoints_array.repeat(3, 0)

        self.max_layers = len(self.layer_stops) - 1
        self.num_layers_to_draw = self.max_layers
        self.arrows_enabled = True
        self.initialized = False
        self.vertex_count = len(self.vertices)

        t_end = time.time()

        logging.info("Initialized Gcode model in %.2f seconds" % (t_end - t_start))
        logging.info("Vertex count: %d" % self.vertex_count)

    def _generate_cylinder(self, start, end, radius, sides):
        """
        Generate vertices and normals for a cylinder between two points.
        Returns (vertices, normals) as lists suitable for GL_TRIANGLES.
        """
        start = numpy.array(start, dtype=float)
        end = numpy.array(end, dtype=float)

        # Calculate direction vector
        direction = end - start
        length = numpy.linalg.norm(direction)

        if length < 1e-6:
            # Degenerate case: zero-length segment, return empty lists
            return [], []

        direction = direction / length

        # Find perpendicular vectors using cross product
        # Choose a vector that's not parallel to direction
        if abs(direction[0]) < 0.9:
            arbitrary = numpy.array([1.0, 0.0, 0.0])
        else:
            arbitrary = numpy.array([0.0, 1.0, 0.0])

        perp1 = numpy.cross(direction, arbitrary)
        perp1 = perp1 / numpy.linalg.norm(perp1)
        perp2 = numpy.cross(direction, perp1)
        perp2 = perp2 / numpy.linalg.norm(perp2)

        # Generate vertices around the circles
        vertices = []
        normals = []

        for i in range(sides):
            angle1 = 2.0 * math.pi * i / sides
            angle2 = 2.0 * math.pi * ((i + 1) % sides) / sides

            # Calculate normals (pointing outward from cylinder axis)
            normal1 = math.cos(angle1) * perp1 + math.sin(angle1) * perp2
            normal2 = math.cos(angle2) * perp1 + math.sin(angle2) * perp2

            # Calculate vertices on start circle
            offset1_start = radius * normal1
            offset2_start = radius * normal2
            v1_start = start + offset1_start
            v2_start = start + offset2_start

            # Calculate vertices on end circle
            offset1_end = radius * normal1
            offset2_end = radius * normal2
            v1_end = end + offset1_end
            v2_end = end + offset2_end

            # Create two triangles for this side of the cylinder
            # Triangle 1: v1_start, v2_start, v1_end
            vertices.extend([v1_start, v2_start, v1_end])
            normals.extend([normal1, normal2, normal1])

            # Triangle 2: v2_start, v2_end, v1_end
            vertices.extend([v2_start, v2_end, v1_end])
            normals.extend([normal2, normal2, normal1])

        return vertices, normals

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
        self.normal_buffer = VBO(self.normals, "GL_STATIC_DRAW")
        self.vertex_color_buffer = VBO(self.colors, "GL_STATIC_DRAW")

        if self.arrows_enabled:
            self.arrow_buffer = VBO(self.arrows, "GL_STATIC_DRAW")
            # For arrows, we need to calculate how many movements we have
            # Each movement has cylinder_sides * 6 vertices
            cylinder_sides = 8
            vertices_per_movement = cylinder_sides * 6
            num_movements = len(self.vertices) // vertices_per_movement
            # Create color buffer for arrows (3 vertices per arrow, one color per movement)
            arrow_colors = []
            for i in range(num_movements):
                color = self.colors[i * vertices_per_movement]
                arrow_colors.extend([color] * 3)
            self.arrow_color_buffer = VBO(numpy.array(arrow_colors, "f"), "GL_STATIC_DRAW")

        self.layer_marker_buffer = VBO(self.layer_markers, "GL_STATIC_DRAW")

        self.initialized = True

    def display(self, elevation=0, eye_height=0, mode_ortho=False, mode_2d=False):
        glPushMatrix()

        offset_z = self.offset_z if not mode_2d else 0
        glTranslate(self.offset_x, self.offset_y, offset_z)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        # Enable lighting for 3D cylinders
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Set up a simple light
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.7, 0.7, 0.7, 1.0])

        self._display_movements(elevation, eye_height, mode_ortho, mode_2d)

        # Display highlights for selected lines
        if len(self.selected_lines) > 0:
            self._display_selection_highlight(elevation, eye_height, mode_ortho, mode_2d)

        # Disable lighting for arrows and markers
        glDisable(GL_LIGHTING)

        if self.arrows_enabled:
            self._display_arrows()

        glDisableClientState(GL_COLOR_ARRAY)

        if self.arrows_enabled:
            self._display_layer_markers()

        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopMatrix()

    def _display_movements(
        self, elevation=0, eye_height=0, mode_ortho=False, mode_2d=False
    ):
        self.vertex_buffer.bind()
        glVertexPointer(3, GL_FLOAT, 0, None)

        self.normal_buffer.bind()
        glNormalPointer(GL_FLOAT, 0, None)

        self.vertex_color_buffer.bind()
        glColorPointer(4, GL_FLOAT, 0, None)

        if mode_2d:
            glScale(1.0, 1.0, 0.0)  # discard z coordinates
            start = self.layer_stops[self.num_layers_to_draw - 1]
            end = self.layer_stops[self.num_layers_to_draw]
            glDrawArrays(GL_TRIANGLES, start, end - start)

        elif mode_ortho:
            if elevation >= 0:
                # draw layers in normal order, bottom to top
                start = 0
                end = self.layer_stops[self.num_layers_to_draw]
                glDrawArrays(GL_TRIANGLES, start, end - start)

            else:
                # draw layers in reverse order, top to bottom
                stop_idx = self.num_layers_to_draw - 1
                while stop_idx >= 0:
                    start = self.layer_stops[stop_idx]
                    end = self.layer_stops[stop_idx + 1]
                    glDrawArrays(GL_TRIANGLES, start, end - start)
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
                glDrawArrays(GL_TRIANGLES, start, end - start)

            if reverse_threshold_layer + 1 < self.num_layers_to_draw:
                # draw layers from the threshold in reverse order, top to bottom
                stop_idx = self.num_layers_to_draw - 1
                while stop_idx > reverse_threshold_layer:
                    start = self.layer_stops[stop_idx]
                    end = self.layer_stops[stop_idx + 1]
                    glDrawArrays(GL_TRIANGLES, start, end - start)
                    stop_idx -= 1

        self.vertex_buffer.unbind()
        self.normal_buffer.unbind()
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

    def set_selected_lines(self, line_numbers):
        """
        Set which Gcode lines are currently selected for highlighting.

        Args:
            line_numbers: Set or list of line numbers (1-indexed)
        """
        self.selected_lines = set(line_numbers) if line_numbers else set()

    def _display_selection_highlight(
        self, elevation=0, eye_height=0, mode_ortho=False, mode_2d=False
    ):
        """
        Render highlighted overlay for selected movements.
        """
        if not self.selected_lines:
            return

        # Find movements that correspond to selected lines
        cylinder_sides = 8
        vertices_per_movement = cylinder_sides * 6

        # Use a brighter, more opaque yellow highlight
        glColor4f(1.0, 1.0, 0.0, 0.8)  # Brighter yellow with more opacity

        # Keep depth test enabled but use polygon offset to draw slightly in front
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(-1.0, -1.0)  # Negative values push towards camera

        # Disable lighting for flat highlight color
        lighting_was_enabled = glIsEnabled(GL_LIGHTING)
        if lighting_was_enabled:
            glDisable(GL_LIGHTING)

        self.vertex_buffer.bind()
        glVertexPointer(3, GL_FLOAT, 0, None)

        # Draw each selected movement
        for movement_idx, line_no in enumerate(self.movement_line_numbers):
            if line_no in self.selected_lines:
                # Calculate vertex range for this movement
                start_vertex = movement_idx * vertices_per_movement
                count = vertices_per_movement

                # Draw the movement geometry with highlight color
                glDrawArrays(GL_TRIANGLES, start_vertex, count)

        self.vertex_buffer.unbind()

        # Restore OpenGL state
        glDisable(GL_POLYGON_OFFSET_FILL)
        if lighting_was_enabled:
            glEnable(GL_LIGHTING)

    def pick_movement(self, x, y, width, height, scene):
        """
        Perform color picking to determine which movement was clicked.

        Args:
            x, y: Mouse coordinates
            width, height: Window dimensions
            scene: Scene object for rendering context

        Returns:
            Line number of clicked movement, or None if no movement was clicked
        """
        from OpenGL.GL import glReadPixels, GL_RGB, GL_UNSIGNED_BYTE

        # Save current OpenGL state
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT | GL_LIGHTING_BIT)

        # Disable lighting and blending for clean color picking
        glDisable(GL_LIGHTING)
        glDisable(GL_BLEND)
        glDisable(GL_DITHER)

        # Clear the buffer
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Set up the same view as the normal rendering
        scene.current_view.begin(width, height)
        scene.current_view.display_transform()

        # Apply model transforms
        glPushMatrix()
        offset_z = self.offset_z if not scene.mode_2d else 0
        glTranslate(self.offset_x, self.offset_y, offset_z)

        # Render each movement with a unique color
        self._render_for_picking()

        # Pop model transform
        glPopMatrix()

        # Read the pixel at the click position
        # Note: OpenGL y-coordinate is inverted
        gl_y = height - y
        pixel = glReadPixels(x, gl_y, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)

        # Clean up view matrices
        scene.current_view.end()

        # Restore OpenGL state
        glPopAttrib()

        # Decode the color to get movement index
        if pixel is not None:
            # Handle different pixel data formats from glReadPixels
            try:
                # On macOS, glReadPixels returns a bytes object
                if isinstance(pixel, bytes):
                    if len(pixel) >= 3:
                        r = pixel[0]
                        g = pixel[1]
                        b = pixel[2]
                    else:
                        return None
                # On other platforms, it may return a numpy array
                else:
                    pixel_flat = numpy.array(pixel).flatten()
                    if len(pixel_flat) >= 3:
                        r = int(pixel_flat[0])
                        g = int(pixel_flat[1])
                        b = int(pixel_flat[2])
                    else:
                        return None
            except (IndexError, TypeError, ValueError):
                return None

            # Background is black (0, 0, 0), so skip it
            if r == 0 and g == 0 and b == 0:
                return None

            # Decode color to movement index (1-based for non-black colors)
            movement_idx = (r << 16) | (g << 8) | b
            movement_idx -= 1  # Convert back to 0-based

            # Get the line number for this movement
            if 0 <= movement_idx < len(self.movement_line_numbers):
                return self.movement_line_numbers[movement_idx]

        return None

    def _render_for_picking(self):
        """
        Render movements with unique colors for picking.
        Each movement gets a unique RGB color based on its index.
        Only renders visible movements (respecting num_layers_to_draw).
        """
        cylinder_sides = 8
        vertices_per_movement = cylinder_sides * 6

        # Only pick within visible layers
        max_visible_vertex = self.layer_stops[self.num_layers_to_draw]
        max_visible_movement = max_visible_vertex // vertices_per_movement

        glEnableClientState(GL_VERTEX_ARRAY)
        self.vertex_buffer.bind()
        glVertexPointer(3, GL_FLOAT, 0, None)

        # Draw each visible movement with a unique color
        for movement_idx in range(max_visible_movement):
            # Encode movement index as RGB color (1-based to avoid black)
            color_id = movement_idx + 1
            r = ((color_id >> 16) & 0xFF) / 255.0
            g = ((color_id >> 8) & 0xFF) / 255.0
            b = (color_id & 0xFF) / 255.0

            glColor3f(r, g, b)

            start_vertex = movement_idx * vertices_per_movement
            glDrawArrays(GL_TRIANGLES, start_vertex, vertices_per_movement)

        self.vertex_buffer.unbind()
        glDisableClientState(GL_VERTEX_ARRAY)

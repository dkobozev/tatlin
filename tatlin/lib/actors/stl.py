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


import numpy
import logging
import time

from OpenGL.GL import *  # type:ignore
from OpenGL.GLE import *  # type:ignore
from OpenGL.arrays.vbo import VBO

from .model import Model

from tatlin.lib import vector


class StlModel(Model):
    """
    Model for displaying and manipulating STL data.
    """

    def load_data(self, model_data, callback=None):
        t_start = time.time()

        vertices, normals = model_data
        # convert python lists to numpy arrays for constructing vbos
        self.vertices = numpy.require(vertices, "f")
        self.normals = numpy.require(normals, "f")

        self.scaling_factor = 1.0
        self.rotation_angle = {
            self.AXIS_X: 0.0,
            self.AXIS_Y: 0.0,
            self.AXIS_Z: 0.0,
        }

        self.mat_specular = (1.0, 1.0, 1.0, 1.0)
        self.mat_shininess = 50.0
        self.light_position = (20.0, 20.0, 20.0)

        self.vertex_count = len(self.vertices)
        self.initialized = False

        t_end = time.time()

        logging.info("Initialized STL model in %.2f seconds" % (t_end - t_start))
        logging.info("Vertex count: %d" % self.vertex_count)

    def normal_data_empty(self):
        """
        Return true if the model has no normal data.
        """
        empty = self.normals.max() == 0 and self.normals.min() == 0
        return empty

    def calculate_normals(self):
        """
        Calculate surface normals for model vertices.
        """
        a = self.vertices[0::3] - self.vertices[1::3]
        b = self.vertices[1::3] - self.vertices[2::3]
        cross = numpy.cross(a, b)

        # normalize the cross product
        magnitudes = numpy.apply_along_axis(numpy.linalg.norm, 1, cross).reshape(-1, 1)
        normals = cross / magnitudes

        # each of 3 facet vertices shares the same normal
        normals = normals.repeat(3, 0)
        return normals

    # ------------------------------------------------------------------------
    # DRAWING
    # ------------------------------------------------------------------------

    def init(self):
        """
        Create vertex buffer objects (VBOs).
        """
        self.vertex_buffer = VBO(self.vertices, "GL_STATIC_DRAW")

        if self.normal_data_empty():
            logging.info("STL model has no normal data")
            self.normals = self.calculate_normals()

        self.normal_buffer = VBO(self.normals, "GL_STATIC_DRAW")
        self.initialized = True

    def draw_facets(self):
        glPushMatrix()

        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glShadeModel(GL_SMOOTH)

        # material properties (white plastic)
        glMaterial(GL_FRONT, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glMaterial(GL_FRONT, GL_DIFFUSE, (0.55, 0.55, 0.55, 1.0))
        glMaterial(GL_FRONT, GL_SPECULAR, (0.7, 0.7, 0.7, 1.0))
        glMaterial(GL_FRONT, GL_SHININESS, 32.0)

        # lights properties
        glLight(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1.0))
        glLight(GL_LIGHT0, GL_DIFFUSE, (0.3, 0.3, 0.3, 1.0))
        glLight(GL_LIGHT1, GL_DIFFUSE, (0.3, 0.3, 0.3, 1.0))

        # lights position
        glLightfv(GL_LIGHT0, GL_POSITION, self.light_position)
        glLightfv(GL_LIGHT1, GL_POSITION, (-20.0, -20.0, 20.0))

        glColor(1.0, 1.0, 1.0)

        # Begin VBO stuff

        self.vertex_buffer.bind()
        glVertexPointer(3, GL_FLOAT, 0, None)
        self.normal_buffer.bind()
        glNormalPointer(GL_FLOAT, 0, None)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)

        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices))

        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        self.normal_buffer.unbind()
        self.vertex_buffer.unbind()

        # End VBO stuff

        glDisable(GL_LIGHT1)
        glDisable(GL_LIGHT0)

        glPopMatrix()

    def display(self, *args, **kwargs):
        glEnable(GL_LIGHTING)
        self.draw_facets()
        glDisable(GL_LIGHTING)

    # ------------------------------------------------------------------------
    # TRANSFORMATIONS
    # ------------------------------------------------------------------------

    def scale(self, factor):
        if factor != self.scaling_factor:
            logging.info("actually scaling vertices")
            self.vertices *= factor / self.scaling_factor
            self.scaling_factor = factor
            self.invalidate_bounding_box()
            self.modified = True

    def translate(self, x, y, z):
        self.vertices = vector.translate(self.vertices, x, y, z)
        self.invalidate_bounding_box()
        self.modified = True

    def rotate_rel(self, angle, axis):
        logging.info(
            "rotating vertices by a relative angle of "
            "%.2f degrees along the %s axis" % (angle, self.axis_letter_map[axis])
        )

        angle = angle % 360
        self.vertices = vector.rotate(self.vertices, angle, *axis)
        self.rotation_angle[axis] += angle
        self.invalidate_bounding_box()
        self.modified = True

    def rotate_abs(self, angle, axis):
        angle = angle % 360
        if self.rotation_angle[axis] == angle:
            return

        logging.info(
            "rotating vertices by an absolute angle of "
            "%.2f degrees along the %s axis" % (angle, self.axis_letter_map[axis])
        )
        final_matrix = vector.identity_matrix()

        # modify matrix to rotate to initial position
        for v in [self.AXIS_Z, self.AXIS_Y, self.AXIS_X]:
            matrix = vector.rotation_matrix(-self.rotation_angle[v], *v)
            final_matrix = final_matrix.dot(matrix)

        # change the angle
        self.rotation_angle[axis] = angle

        # modify matrix to rotate to new position
        for v in [self.AXIS_X, self.AXIS_Y, self.AXIS_Z]:
            matrix = vector.rotation_matrix(self.rotation_angle[v], *v)
            final_matrix = final_matrix.dot(matrix)

        self.vertices = self.vertices.dot(final_matrix)
        self.invalidate_bounding_box()
        self.modified = True

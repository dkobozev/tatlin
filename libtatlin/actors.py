from __future__ import division

import math
import numpy

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLUT import *
from OpenGL.arrays.vbo import VBO

import vector


def compile_display_list(func, *options):
    display_list = glGenLists(1)
    glNewList(display_list, GL_COMPILE)
    func(*options)
    glEndList()
    return display_list


class Platform(object):
    # makerbot platform size
    width = 120
    depth = 100
    grid  = 10

    def __init__(self):
        self.color_guides = (0xaf / 255, 0xdf / 255, 0x5f / 255, 0.4)
        self.color_fill   = (0xaf / 255, 0xdf / 255, 0x5f / 255, 0.1)
        self.initialized = False

    def init(self):
        self.display_list = compile_display_list(self.draw)
        self.initialized = True

    def draw(self):
        glPushMatrix()

        glTranslate(-self.width / 2, -self.depth / 2, 0)
        glColor(*self.color_guides)

        # draw the grid
        glBegin(GL_LINES)
        for i in range(0, self.width + self.grid, self.grid):
            glVertex3f(float(i), 0.0,        0.0)
            glVertex3f(float(i), self.depth, 0.0)

        for i in range(0, self.depth + self.grid, self.grid):
            glVertex3f(0,          float(i), 0.0)
            glVertex3f(self.width, float(i), 0.0)
        glEnd()

        # draw fill
        glColor(*self.color_fill)
        glRectf(0.0, 0.0, float(self.width), float(self.depth))

        glPopMatrix()

    def display(self):
        glCallList(self.display_list)


class GcodeModel(object):
    color_map = {
        'red':    [1.0, 0.0, 0.0, 0.6],
        'yellow': [1.0, 0.875, 0.0, 0.6],
        'orange': [1.0, 0.373, 0.0, 0.6],
        'green':  [0.0, 1.0, 0.0, 0.6],
        'cyan':   [0.0, 0.875, 0.875, 0.6],
        'gray':   [0.5, 0.5, 0.5, 0.5],
    }

    arrow = numpy.require([
        [0.0, 0.0, 0.0],
        [0.4, -0.2, 0.0],
        [0.4, 0.2, 0.0],
    ], 'f')

    def __init__(self, model_data):
        self.create_vertex_arrays(model_data)

        self.max_layers = len(self.layer_stops)
        self.num_layers_to_draw = self.max_layers
        self.arrows_enabled = True
        self.initialized = False

        print '!!! Gcode model, vertex count:', len(self.vertices)

    def create_vertex_arrays(self, model_data):
        vertex_list = []
        color_list = []
        self.layer_stops = [] # indexes at which layers end
        arrow_list = []

        for layer in model_data:
            for movement in layer:
                a, b = movement.point_a, movement.point_b
                vertex_list.append([a.x, a.y, a.z])
                vertex_list.append([b.x, b.y, b.z])

                arrow = vector.rotate(self.arrow, movement.angle(), 0.0, 0.0, 1.0)
                arrow = vector.translate(arrow, b.x, b.y, b.z)
                arrow_list.extend(arrow)

                vertex_color = self.movement_color(movement)
                color_list.append(vertex_color)

            self.layer_stops.append(len(vertex_list))

        self.vertices = numpy.require(vertex_list, 'f')
        self.colors = numpy.require(color_list, 'f')
        self.arrows = numpy.require(arrow_list, 'f')

        # for every pair of vertices of the model, there are 3 vertices for the arrow
        assert len(self.arrows) == ((len(self.vertices) // 2) * 3)

    def init(self):
        """
        Create a display list for each model layer.
        """
        self.vertex_buffer       = VBO(self.vertices, 'GL_STATIC_DRAW')
        self.vertex_color_buffer = VBO(self.colors.repeat(2, 0), 'GL_STATIC_DRAW') # each pair of vertices shares the color
        self.arrow_buffer        = VBO(self.arrows, 'GL_STATIC_DRAW')
        self.arrow_color_buffer  = VBO(self.colors.repeat(3, 0), 'GL_STATIC_DRAW') # each triplet of vertices shares the color
        self.initialized = True

    def draw_arrows(self, layer, list_container=None):
        if list_container is None:
            list_container = []

        layer_arrow_list = compile_display_list(self._draw_arrows, layer)
        list_container.append(layer_arrow_list)

        return list_container

    def _draw_arrows(self, layer):
        for movement in layer:
            self.draw_arrow(movement)

    def draw_arrow(self, movement):
        a, b = movement.points()
        angle = self.points_angle(a, b)

        glPushMatrix()

        glTranslate(b.x, b.y, b.z)
        glRotate(angle, 0.0, 0.0, 1.0)
        glColor(*self.movement_color(movement))

        glBegin(GL_TRIANGLES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.4, -0.2, 0.0)
        glVertex3f(0.4, 0.2, 0.0)
        glEnd()

        glPopMatrix()

    def movement_color(self, movement):
        if not movement.extruder_on:
            color = self.color_map['gray']
        elif movement.is_loop:
            color = self.color_map['yellow']
        elif movement.is_perimeter and movement.is_perimeter_outer:
            color = self.color_map['cyan']
        elif movement.is_perimeter:
            color = self.color_map['green']
        else:
            color = self.color_map['red']

        return color

    def display(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        self._display_movements()
        self._display_arrows()

        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)

    def _display_movements(self):
        self.vertex_buffer.bind()
        glVertexPointer(3, GL_FLOAT, 0, None)

        self.vertex_color_buffer.bind()
        glColorPointer(4, GL_FLOAT, 0, None)

        glDrawArrays(GL_LINES, 0, self.layer_stops[self.num_layers_to_draw - 1])

        self.vertex_buffer.unbind()
        self.vertex_color_buffer.unbind()

    def _display_arrows(self):
        self.arrow_buffer.bind()
        glVertexPointer(3, GL_FLOAT, 0, None)

        self.arrow_color_buffer.bind()
        glColorPointer(4, GL_FLOAT, 0, None)

        layer_idx = self.num_layers_to_draw - 1
        if layer_idx > 0:
            start = (self.layer_stops[layer_idx - 1] // 2) * 3
        else:
            start = 0
        end = (self.layer_stops[layer_idx] // 2) * 3

        glDrawArrays(GL_TRIANGLES, start, end - start)

        self.arrow_buffer.unbind()
        self.arrow_color_buffer.unbind()


class StlModel(object):
    def __init__(self, model_data):
        vertices, normals = model_data
        # convert python lists to numpy arrays for constructing vbos
        self.vertices = numpy.require(vertices, 'f')
        self.normals  = numpy.require(normals, 'f')

        self.display_list = None

        self.mat_specular = (1.0, 1.0, 1.0, 1.0)
        self.mat_shininess = 50.0
        self.light_position = (20.0, 20.0, 20.0)
        self.scaling_factor = 1.0

        self.max_layers = 42

        self.initialized = False

    def init(self):
        """
        Create vertex buffer objects (VBOs).
        """
        self.vertex_buffer = VBO(self.vertices, 'GL_STATIC_DRAW')
        self.normal_buffer = VBO(self.normals, 'GL_STATIC_DRAW')
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

        ### VBO stuff

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

        ### end VBO stuff

        glDisable(GL_LIGHT1)
        glDisable(GL_LIGHT0)

        glPopMatrix()

    def scale(self, factor):
        self.vertices *= factor

    def display(self):
        glEnable(GL_LIGHTING)
        self.draw_facets()
        glDisable(GL_LIGHTING)


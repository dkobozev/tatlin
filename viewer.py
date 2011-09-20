#!/usr/bin/env python2

from __future__ import division

import pygtk
pygtk.require('2.0')
from gtk.gtkgl.apputils import *

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLUT import *

from skein import gcodec
from skein.vector3 import Vector3

import math


def line_slope(a, b):
    slope = (b.y - a.y) / (b.x - a.x)
    return slope


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

class Gcode(object):

    marker_layer                  = '(<layer>'
    marker_perimeter_start        = '(<perimeter>'
    marker_perimeter_end          = '(</perimeter>)'
    marker_loop_start             = '(<loop>'
    marker_loop_end               = '(</loop>)'
    marker_surrounding_loop_start = '(<surroundingLoop>)'
    marker_surrounding_loop_end   = '(</surroundingLoop>)'

    def __init__(self, fname):
        self.fname = fname
        self.gcode_lines = self.split(self.read())

        self.is_new_layer = self.is_new_layer_from_marker if self.file_has_layer_markers() else self.is_new_layer_from_gcode

        self.prev_location = Vector3(Platform.width / 2, -Platform.depth / 2, 10.0)

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

    def parse_layers(self):
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

class Platform(object):
    # makerbot platform size
    width = 120
    depth = 100
    grid  = 10

    def __init__(self):
        self.color_guides = (0xaf / 255, 0xdf / 255, 0x5f / 255, 0.4)
        self.color_fill   = (0xaf / 255, 0xdf / 255, 0x5f / 255, 0.1)

    def init(self):
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        self.draw()
        glEndList()

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


class Model(object):
    def __init__(self, layers):
        self.layers = layers
        self.max_layers = len(self.layers)
        self.num_layers_to_draw = self.max_layers
        self.arrows_enabled = True

        self.colors = {
            'red':    (1.0, 0.0, 0.0, 0.6),
            'yellow': (1.0, 0.875, 0.0, 0.6),
            'orange': (1.0, 0.373, 0.0, 0.6),
            'green':  (0.0, 1.0, 0.0, 0.6),
            'cyan':   (0.0, 0.875, 0.875, 0.6),
            'gray':   (0.5, 0.5, 0.5, 0.5),
        }

        line_count = 0
        for layer in self.layers:
            line_count += len(layer)
        print '!!! line count:     ', line_count
        print '!!! lines per layer:', round(line_count / self.max_layers)

    def init(self):
        """
        Create a display list for each model layer.
        """
        self.display_lists = self.draw_layers()

        self.arrow_lists = []
        if self.arrows_enabled:
            for layer in self.layers:
                self.draw_arrows(layer, self.arrow_lists)

    def draw_layers(self, list_container=None):
        if list_container is None:
            list_container = []


        for layer_no, layer in enumerate(self.layers):
            layer_list = glGenLists(1)
            glNewList(layer_list, GL_COMPILE)

            glPushMatrix()
            glRotate(180, 0.0, 0.0, 1.0)
            self.draw_layer(layer, (layer_no == self.num_layers_to_draw - 1))
            glPopMatrix()

            glEndList()
            list_container.append(layer_list)

        return list_container

    def draw_layer(self, layer, last=False):
        for movement in layer:
            glColor(*self.movement_color(movement))

            point_a = movement.point_a
            point_b = movement.point_b

            glBegin(GL_LINES)
            glVertex3f(point_a.x, point_a.y, point_a.z)
            glVertex3f(point_b.x, point_b.y, point_b.z)
            glEnd()

    def draw_arrows(self, layer, list_container=None):
        if list_container is None:
            list_container = []

        layer_arrow_list = glGenLists(1)
        glNewList(layer_arrow_list, GL_COMPILE)

        for movement in layer:
            color = self.movement_color(movement)
            glColor(*color)
            self.draw_arrow(movement)

        glEndList()
        list_container.append(layer_arrow_list)

        return list_container

    def draw_arrow(self, movement):
        a = movement.point_a
        b = movement.point_b

        try:
            slope = line_slope(a, b)
            angle = math.degrees(math.atan(slope))
            if b.x > a.x:
                angle = 180 + angle
        except ZeroDivisionError:
            angle = 90
            if b.y > a.y:
                angle = 180 + angle

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
            color = self.colors['gray']
        elif movement.is_loop:
            color = self.colors['yellow']
        elif movement.is_perimeter and movement.is_perimeter_outer:
            color = self.colors['cyan']
        elif movement.is_perimeter:
            color = self.colors['green']
        else:
            color = self.colors['red']

        return color

    def display(self):
        for layer in self.display_lists[:self.num_layers_to_draw]:
            glCallList(layer)

        if self.arrows_enabled:
            glCallList(self.arrow_lists[self.num_layers_to_draw - 1])


class Canvas(GLScene, GLSceneButton, GLSceneButtonMotion):
    def __init__(self):
        GLScene.__init__(self, gtk.gdkgl.MODE_RGB | gtk.gdkgl.MODE_DEPTH | gtk.gdkgl.MODE_DOUBLE)

        self.actors = []

        self.begin_x = 0
        self.begin_y = 0

        self.__sphi = 180.0
        self.__stheta = 80.0

        self.obj_pos = [0.0, 0.0, -5.0]

    def init(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHT0)

        # simulate translucency by blending colors
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glutInit()
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)

        for actor in self.actors:
            actor.init()

    def display(self, width, height):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glLoadIdentity()
        glTranslatef(*self.obj_pos)
        glRotatef(-self.__stheta, 1.0, 0.0, 0.0)
        glRotatef(self.__sphi, 0.0, 0.0, 1.0)

        for actor in self.actors:
            actor.display()

        glFlush()

    def reshape(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(80.0, width / height, 0, 20.0)
        glMatrixMode(GL_MODELVIEW)

    def button_press(self, width, height, event):
        self.begin_x = event.x
        self.begin_y = event.y

    def button_release(self, width, height, event):
        pass

    def button_motion(self, width, height, event):
        if event.state & gtk.gdk.BUTTON1_MASK: # left mouse button
            self.__sphi += (event.x - self.begin_x) / 4.0
            self.__stheta += (self.begin_y - event.y) / 4.0
        elif event.state & gtk.gdk.BUTTON2_MASK: # middle mouse button
            self.obj_pos[2] += (self.begin_y - event.y) / 10.0
        elif event.state & gtk.gdk.BUTTON3_MASK: # right mouse button
            self.obj_pos[0] -= (self.begin_x - event.x) / 50.0
            self.obj_pos[1] += (self.begin_y - event.y) / 50.0

        self.begin_x = event.x
        self.begin_y = event.y

        self.invalidate()


class ViewerWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title('viewer')
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        gcode = Gcode(sys.argv[1])

        platform = Platform()
        self.model = Model(gcode.parse_layers())

        self.canvas = Canvas()
        self.canvas.actors.append(platform)
        self.canvas.actors.append(self.model)
        self.glarea = GLArea(self.canvas)

        label_layers = gtk.Label('Layers')
        self.scale_layers = gtk.HScale()
        self.scale_layers.set_range(1, self.model.max_layers)
        self.scale_layers.set_value(self.model.max_layers)
        self.scale_layers.set_increments(1, 10)
        self.scale_layers.set_digits(0)
        self.scale_layers.set_size_request(200, 35)
        self.scale_layers.connect('value-changed', self.on_scale_value_changed)

        table_layers = gtk.Table(rows=2, columns=1)
        table_layers.set_border_width(5)
        table_layers.set_row_spacings(5)
        table_layers.attach(label_layers,      0, 1, 0, 1, yoptions=0)
        table_layers.attach(self.scale_layers, 0, 1, 1, 2, yoptions=0)

        frame_layers = gtk.Frame()
        frame_layers.add(table_layers)

        vbox = gtk.VBox()
        vbox.pack_start(frame_layers)

        hbox = gtk.HBox()
        hbox.pack_start(self.glarea, expand=True,  fill=True)
        hbox.pack_start(vbox,        expand=False, fill=False)
        self.add(hbox)

        self.connect('destroy', lambda quit: gtk.main_quit())
        self.connect('key-press-event', self.on_keypress)

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            gtk.main_quit()

    def on_scale_value_changed(self, widget):
        value = int(widget.get_value())
        self.model.num_layers_to_draw = value
        self.canvas.invalidate()


if __name__ == '__main__':
    window = ViewerWindow()
    window.show_all()
    gtk.main()

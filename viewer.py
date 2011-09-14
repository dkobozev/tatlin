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


class Gcode(object):

    layer_marker = '(<layer>'

    def __init__(self, fname):
        self.fname = fname
        self.gcode_lines = self.split(self.read())

        self.is_new_layer = self.is_new_layer_from_marker if self.file_has_layer_markers() else self.is_new_layer_from_gcode

        self.prev_location = Vector3(0.0, 0.0, 0.0)
        self.extruder_on = False

    def split(self, s):
        lines = s.replace('\r', '\n').replace('\n\n', '\n').split('\n')
        return lines

    def read(self):
        f = open(self.fname, 'r')
        content = f.read()
        f.close()
        return content

    def locations(self):
        locations = []
        layer = []
        for line in self.gcode_lines:
            split_line = gcodec.getSplitLineBeforeBracketSemicolon(line)

            if len(split_line) < 1:
                continue

            if self.is_new_layer(split_line): # start new layer if necessary
                locations.append(layer)
                layer = []

            location = self.parse_location(split_line)
            if location != self.prev_location:
                layer.append((self.prev_location, location, self.extruder_on))
                self.prev_location = location

        locations.append(layer)
        return locations

    def parse_location(self, split_line):
        first_word = split_line[0]
        location = self.prev_location
        if first_word == 'G1': # linear travel
            location = gcodec.getLocationFromSplitLine(self.prev_location, split_line)
        elif first_word == 'M101': # turn extruder forward
            self.extruder_on = True
        elif first_word == 'M103': # turn extruder off
            self.extruder_on = False

        return location

    def file_has_layer_markers(self):
        has_markers = gcodec.isThereAFirstWord(self.layer_marker, self.gcode_lines, 1)
        return has_markers

    def is_new_layer_from_marker(self, split_line):
        return split_line[0] == self.layer_marker

    def is_new_layer_from_gcode(self, split_line):
        is_new_layer = False

        if split_line[0] in ('G1', 'G2', 'G3'):
            new_location = gcodec.getLocationFromSplitLine(self.prev_location, split_line)
            if new_location.z - self.prev_location.z > 0.1:
                is_new_layer = True

        return is_new_layer

class Platform(object):

    def __init__(self):
        self.color_guides = (0xaf / 255, 0xdf / 255, 0x5f / 255)
        self.color_fill   = (0xaf / 255, 0xdf / 255, 0x5f / 255, 0.2)

        self.width = 10
        self.depth = 10
        self.grid  = 1

    def init(self):
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        self.draw()
        glEndList()

    def draw(self):
        glColor(*self.color_guides)

        # draw the grid
        glBegin(GL_LINES)
        for i in range(0, self.width + self.grid, self.grid):
            glVertex3f(float(i), 0.0,        0.0)
            glVertex3f(float(i), self.depth, 0.0)

            glVertex3f(0,          float(i), 0.0)
            glVertex3f(self.width, float(i), 0.0)
        glEnd()

        # simulate translucency by blending colors
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # draw fill
        glColor(*self.color_fill)
        glRectf(0.0, 0.0, float(self.width), float(self.depth))

    def display(self):
        glCallList(self.display_list)


class Model(object):

    def __init__(self, locations):
        self.locations = locations
        self.max_layers = len(self.locations)
        self.draw_layers = self.max_layers

        self.color_top_layer    = (1.0, 0.0, 0.0, 1.0)
        self.color_extruder_on  = (1.0, 0.0, 0.0, 0.6)
        self.color_extruder_off = (0.5, 0.5, 0.5, 0.5)

        line_count = 0
        for layer in self.locations:
            line_count += len(layer)
        print '!!! line count:', line_count

    def init(self):
        self.display_lists = []
        for layer_no, layer in enumerate(self.locations):
            layer_list = glGenLists(1)
            glNewList(layer_list, GL_COMPILE)
            self.draw_layer(layer, layer_no)
            glEndList()
            self.display_lists.append(layer_list)

    def draw_layer(self, layer, layer_no):
        glBegin(GL_LINES)
        for location in layer:
            v1, v2, extruder_on = location

            if extruder_on:
                if layer_no == self.max_layers - 1:
                    glColor(*self.color_top_layer)
                else:
                    glColor(*self.color_extruder_on)
            else:
                glColor(*self.color_extruder_off)

            glVertex3f(v1.x, v1.y, v1.z)
            glVertex3f(v2.x, v2.y, v2.z)
        glEnd()

    def display(self):
        for layer in self.display_lists[:self.draw_layers]:
            glCallList(layer)


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

        #glHint(GL_LINE_SMOOTH_HINT, GL_FASTEST)
        #glEnable(GL_LINE_SMOOTH)
        #glLineWidth(5)
        #glBegin(GL_LINES)
        #for layer_no, layer in enumerate(self.locations[:self.max_layers]):
        #    for location in layer:
        #        v1, v2, extruder_on = location

        #        if extruder_on:
        #            glColor4f(1.0, 0.0, 0.0, 0.1)
        #        else:
        #            glColor4f(0.5, 0.5, 0.5, 0.1)

        #        glVertex3f(v1.x, v1.y, v1.z)
        #        glVertex3f(v2.x, v2.y, v2.z)
        #glEnd()

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
        self.model = Model(gcode.locations())

        self.canvas = Canvas()
        self.canvas.actors.append(platform)
        self.canvas.actors.append(self.model)
        self.glarea = GLArea(self.canvas)

        label_layers = gtk.Label('Layers')
        self.scale_layers = gtk.HScale()
        self.scale_layers.set_range(0, self.model.max_layers)
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
        self.model.draw_layers = value
        self.canvas.invalidate()


if __name__ == '__main__':
    window = ViewerWindow()
    window.show_all()
    gtk.main()

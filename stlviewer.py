#!/usr/bin/env python2

from __future__ import division

import pygtk
pygtk.require('2.0')
from gtk.gtkgl.apputils import *

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLUT import *

from skein.vector3 import Vector3

import math

from stlparser import StlAsciiParser


def line_slope(a, b):
    slope = (b.y - a.y) / (b.x - a.x)
    return slope

def paginate(sequence, n):
    """
    Yield n-sized pieces of sequence.
    """
    for i in range(0, len(sequence), n):
        yield sequence[i:i+n]

def html_color(color):
    if color.startswith('#'):
        color = color[1:]
    parsed = [int(c, 16) / 255 for c in paginate(color, 2)]
    return parsed


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
    def __init__(self, facets):
        self.facets = facets

        self.mat_specular = (1.0, 1.0, 1.0, 1.0)
        self.mat_shininess = 50.0

    def init(self):
        """
        Create a display list.
        """
        self.draw_facets()

    def draw_facets(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)

        glMaterial(GL_FRONT, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glMaterial(GL_FRONT, GL_DIFFUSE, (0.55, 0.55, 0.55, 1.0))
        glMaterial(GL_FRONT, GL_SPECULAR, (0.7, 0.7, 0.7, 1.0))
        glMaterial(GL_FRONT, GL_SHININESS, 32.0)

        glLight(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1.0))
        glLight(GL_LIGHT0, GL_DIFFUSE, (0.3, 0.3, 0.3, 1.0))

        glLight(GL_LIGHT1, GL_DIFFUSE, (0.3, 0.3, 0.3, 1.0))

        glColor(1.0, 1.0, 1.0)
        for facet in self.facets:
            self.draw_facet(facet)

        glEndList()
        self.display_list = display_list

    def draw_facet(self, facet):
        normal = facet.normal
        v1, v2, v3 = facet.vertices[0], facet.vertices[1], facet.vertices[2]

        glBegin(GL_POLYGON)
        glNormal3f(normal.x, normal.y, normal.z)
        glVertex3f(v1.x, v1.y, v1.z)
        glVertex3f(v2.x, v2.y, v2.z)
        glVertex3f(v3.x, v3.y, v3.z)
        glEnd()

    def display(self):
        glCallList(self.display_list)


class Scene(GLScene, GLSceneButton, GLSceneButtonMotion):
    def __init__(self):
        GLScene.__init__(self, gtk.gdkgl.MODE_RGB | gtk.gdkgl.MODE_DEPTH | gtk.gdkgl.MODE_DOUBLE)

        self.actors = []

        self.begin_x = 0
        self.begin_y = 0

        self.obj_pos = Vector3(0.0, 180.0, -20.0)
        self.light_position = (20.0, 20.0, 20.0)

        self.__sphi   = 0.0
        self.__stheta = -20.0
        self.fovy     = 80.0
        self.z_near   = 1.0
        self.z_far    = 9000.0 # very far

    def init(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glShadeModel(GL_SMOOTH)

        # simulate translucency by blending colors
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glutInit()
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)

        print '!!! initializing actors'
        print '!!! actors:', len(self.actors)
        for actor in self.actors:
            actor.init()

    def display(self, width, height):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glLoadIdentity()
        glRotate(-90, 1.0, 0.0, 0.0) # make z point up

        glLightfv(GL_LIGHT0, GL_POSITION, self.light_position)
        glLightfv(GL_LIGHT1, GL_POSITION, (-20.0, -20.0, 20.0))

        glDisable(GL_CULL_FACE)
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        self.view_ortho(width, height)

        self.draw_axes()

        self.view_perspective()
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

        glTranslatef(self.obj_pos.x, self.obj_pos.y, self.obj_pos.z)
        glRotatef(-self.__stheta, 1.0, 0.0, 0.0)
        glRotatef(self.__sphi, 0.0, 0.0, 1.0)

        for actor in self.actors:
            actor.display()

        glFlush()

    def view_ortho(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, 0, height, -100.0, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def view_perspective(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def reshape(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fovy, width / height, self.z_near, self.z_far)
        glMatrixMode(GL_MODELVIEW)

    def button_press(self, width, height, event):
        self.begin_x = event.x
        self.begin_y = event.y

    def button_release(self, width, height, event):
        pass

    def button_motion(self, width, height, event):
        delta_x = event.x - self.begin_x
        delta_y = event.y - self.begin_y

        if event.state & gtk.gdk.BUTTON1_MASK: # left mouse button
            self.rotate(delta_x, delta_y)
        elif event.state & gtk.gdk.BUTTON2_MASK: # middle mouse button
            self.zoom(delta_x, delta_y)
        elif event.state & gtk.gdk.BUTTON3_MASK: # right mouse button
            self.pan(delta_x, delta_y, width, height)

        self.begin_x = event.x
        self.begin_y = event.y

        self.invalidate()

    def rotate(self, delta_x, delta_y):
        self.__sphi   += delta_x / 4.0
        self.__stheta -= delta_y / 4.0

    def zoom(self, delta_x, delta_y):
        self.obj_pos.y += delta_y / 10.0

    def pan(self, delta_x, delta_y, width, height):
        """
        Pan the model.

        Pannings works by translating relating mouse movements to movements in object space,
        using program window dimensions and field of view angle. A factor is applied to avoid
        speeding up on rapid mouse movements.
        """
        window_h = 2 * abs(self.obj_pos) * math.tan(self.fovy / 2) # height of window in object space

        magnitude_x = abs(delta_x)
        if magnitude_x > 0.0:
            x_scale = magnitude_x / width
            x_slow = 1 / magnitude_x
            self.obj_pos.x -= delta_x * x_scale * window_h * x_slow

        magnitude_y = abs(delta_y)
        if magnitude_y > 0.0:
            y_scale = magnitude_y / width
            y_slow = 1 / magnitude_y
            self.obj_pos.z += delta_y * y_scale * window_h * y_slow

    def draw_axes(self, length=50.0):
        glPushMatrix()

        glRotate(-90, 1.0, 0.0, 0.0) # make z point up
        glTranslatef(length + 20.0, 0.0, length + 20.0)
        glRotatef(-self.__stheta, 1.0, 0.0, 0.0)
        glRotatef(self.__sphi, 0.0, 0.0, 1.0)

        glBegin(GL_LINES)
        glColor(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(-length, 0.0, 0.0)

        glColor(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, -length, 0.0)

        glColor(*html_color('008aff'))
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, length)
        glEnd()

        glPopMatrix()


class ViewerWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title('viewer')
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        parser = StlAsciiParser(sys.argv[1])

        platform = Platform()
        self.model = Model(parser.parse())

        self.scene = Scene()
        self.scene.actors.append(self.model)
        # platform has to be added last to be translucent
        self.scene.actors.append(platform)
        self.glarea = GLArea(self.scene)

        label_layers = gtk.Label('Layers')
        self.scale_layers = gtk.HScale()
        self.scale_layers.set_range(1, 10)
        self.scale_layers.set_value(1)
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
        pass


if __name__ == '__main__':
    window = ViewerWindow()
    window.show_all()
    gtk.main()

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


from __future__ import division

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import pygtk
pygtk.require('2.0')
import gtk
from gtk.gtkgl.apputils import GLArea, GLScene, GLSceneButton, GLSceneButtonMotion

from .actors import Model
from .views import View2D, View3D


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


class SceneArea(GLArea):
    """
    Extend GLScene to provide mouse wheel support.
    """
    def __init__(self, *args, **kwargs):
        super(SceneArea, self).__init__(*args, **kwargs)

        self.connect('scroll-event', self.glscene.wheel_scroll)
        self.add_events(gtk.gdk.SCROLL_MASK)


class Scene(GLScene, GLSceneButton, GLSceneButtonMotion):
    """
    A scene is responsible for displaying a model and accompanying objects (actors).

    In addition to calling display functions on its actors, the scene is also
    responsible for viewing transformations such as zooming, panning and
    rotation, as well as being the interface for the actors.
    """
    PAN_SPEED    = 25
    ROTATE_SPEED = 25

    def __init__(self):
        super(Scene, self).__init__(gtk.gdkgl.MODE_RGB |
                                    gtk.gdkgl.MODE_DEPTH |
                                    gtk.gdkgl.MODE_DOUBLE)
        self.model    = None
        self.actors   = []
        self.cursor_x = 0
        self.cursor_y = 0

        self.view_ortho = View2D()
        self.view_perspective = View3D()
        self.current_view = self.view_perspective

        self.initialized = False

        # dict of scene properties
        self._scene_properties = {
            'max_layers':     lambda: self.model.max_layers,
            'scaling-factor': lambda: round(self.model.scaling_factor, 2),
            'width':          lambda: self.model.width,
            'depth':          lambda: self.model.depth,
            'height':         lambda: self.model.height,
            'rotation-x':     lambda: self.model.rotation_angle[self.model.AXIS_X],
            'rotation-y':     lambda: self.model.rotation_angle[self.model.AXIS_Y],
            'rotation-z':     lambda: self.model.rotation_angle[self.model.AXIS_Z],
        }

    def add_model(self, model):
        self.model = model
        self.actors.append(self.model)

    def export_to_file(self, model_file):
        """
        Write model to file.
        """
        model_file.write_stl(self.model)
        self.model.modified = False

    def add_supporting_actor(self, actor):
        self.actors.append(actor)

    def clear(self):
        self.actors = []

    def is_initialized(self):
        return self.glarea.window is not None

    # ------------------------------------------------------------------------
    # DRAWING
    # ------------------------------------------------------------------------

    def init(self):
        glClearColor(0.0, 0.0, 0.0, 0.0) # set clear color to black
        glClearDepth(1.0)                # set depth value to 1
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        # simulate translucency by blending colors
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.init_actors()
        self.initialized = True

    def init_actors(self):
        for actor in self.actors:
            if not actor.initialized:
                actor.init()

    def display(self, w, h):
        # clear the color and depth buffers from any leftover junk
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # discard back-facing polygons
        glCullFace(GL_BACK)

        # fix normals after scaling to prevent problems with lighting
        # see: http://www.opengl.org/resources/faq/technical/lights.htm#ligh0090
        glEnable(GL_RESCALE_NORMAL)

        self.view_ortho.begin(w, h)
        self.draw_axes()
        self.view_ortho.end()

        self.current_view.begin(w, h)
        self.current_view.display_transform()
        for actor in self.actors:
            actor.display(self.mode_2d)
        self.current_view.end()

    def reshape(self, w, h):
        glViewport(0, 0, w, h)

    def draw_axes(self, length=50.0):
        glPushMatrix()
        self.current_view.ui_transform(length)

        axes = [
            (-length, 0.0, 0.0),
            (0.0, -length, 0.0),
            (0.0, 0.0, length),
        ]
        colors = [
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            html_color('008aff')
        ]
        labels = ['x', 'y', 'z']

        glBegin(GL_LINES)

        for axis, color in zip(axes, colors):
            glColor(*color)
            glVertex(0.0, 0.0, 0.0)
            glVertex(*axis)

        glEnd()

        # draw axis labels
        glutInit()

        for label, axis, color in zip(labels, axes, colors):
            glColor(*color)
            # add padding to labels
            glRasterPos(axis[0] + 2, axis[1] + 2, axis[2] + 2)
            glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(label));

        glPopMatrix()

    # ------------------------------------------------------------------------
    # VIEWING MANIPULATIONS
    # ------------------------------------------------------------------------

    def button_press(self, width, height, event):
        self.cursor_x = event.x
        self.cursor_y = event.y

    def button_release(self, width, height, event):
        pass

    def button_motion(self, width, height, event):
        delta_x = event.x - self.cursor_x
        delta_y = event.y - self.cursor_y

        if event.state & gtk.gdk.BUTTON1_MASK: # left mouse button
            self.current_view.rotate(delta_x * self.ROTATE_SPEED / 100,
                                     delta_y * self.ROTATE_SPEED / 100)
        elif event.state & gtk.gdk.BUTTON2_MASK: # middle mouse button
            if hasattr(self.current_view, 'offset'):
                self.current_view.offset(delta_x * self.PAN_SPEED / 100,
                                         delta_y * self.PAN_SPEED / 100)
        elif event.state & gtk.gdk.BUTTON3_MASK: # right mouse button
            self.current_view.pan(delta_x * self.PAN_SPEED / 100,
                                  delta_y * self.PAN_SPEED / 100)

        self.cursor_x = event.x
        self.cursor_y = event.y

        self.invalidate()

    def wheel_scroll(self, widget, event):
        delta_y = 30.0
        if event.direction == gtk.gdk.SCROLL_DOWN:
            delta_y = -delta_y

        self.current_view.zoom(0, delta_y)
        self.invalidate()

    def reset_view(self, both=False):
        if both:
            self.view_ortho.reset_state()
            self.view_perspective.reset_state()
        else:
            self.current_view.reset_state()

    @property
    def mode_2d(self):
        return isinstance(self.current_view, View2D)

    @mode_2d.setter
    def mode_2d(self, value):
        self.current_view = self.view_ortho if value else self.view_perspective

    @property
    def mode_ortho(self):
        return self.current_view.supports_ortho and self.current_view.ortho

    @mode_ortho.setter
    def mode_ortho(self, value):
        if self.current_view.supports_ortho:
            self.current_view.ortho = value

    def rotate_view(self, azimuth, elevation):
        if not self.mode_2d:
            self.current_view.azimuth = azimuth
            self.current_view.elevation = elevation
            self.invalidate()

    # ------------------------------------------------------------------------
    # MODEL MANIPULATION
    # ------------------------------------------------------------------------

    def change_num_layers(self, number):
        """
        Change number of visible layers for Gcode model.
        """
        self.model.num_layers_to_draw = number

    def scale_model(self, factor):
        print '--- scaling model by factor of:', factor
        self.model.scale(factor)
        self.model.init()

    def center_model(self):
        """
        Center the model on platform and raise its lowest point to z=0.
        """
        bounding_box = self.model.bounding_box
        lower_corner = bounding_box.lower_corner
        upper_corner = bounding_box.upper_corner
        offset_x = -(upper_corner[0] + lower_corner[0]) / 2
        offset_y = -(upper_corner[1] + lower_corner[1]) / 2
        offset_z = -lower_corner[2]
        self.model.translate(offset_x, offset_y, offset_z)
        self.model.init()

    def change_model_dimension(self, dimension, value):
        current_value = getattr(self.model, dimension)
        # since our scaling is absolute, we have to take current scaling factor
        # into account
        factor = (value / current_value) * self.model.scaling_factor
        self.scale_model(factor)

    def rotate_model(self, angle, axis_name):
        axis = Model.letter_axis_map[axis_name]
        self.model.rotate_abs(angle, axis)
        self.model.init()

    def get_property(self, name):
        """
        Return a property of the scene, e.g number of layers in the current model.
        """
        return self._scene_properties[name]()

    def show_arrows(self, show):
        self.model.arrows_enabled = show
        self.model.init()

    @property
    def model_modified(self):
        """
        Return true when an important model property has been modified.

        Important properties exclude viewing transformations and can be
        something like size, shape or color.
        """
        return self.model and self.model.modified


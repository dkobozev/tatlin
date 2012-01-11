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

import math

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import pygtk
pygtk.require('2.0')
import gtk
from gtk.gtkgl.apputils import GLArea, GLScene, GLSceneButton, GLSceneButtonMotion

from .vector3 import Vector3
from .actors import Model


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


class ViewMode(object):
    """
    Base class for projection transformations.
    """
    ZOOM_MIN = 0.1
    ZOOM_MAX = 1000

    def __init__(self):
        self._stack = []
        self._save_vars = []

    def push_state(self):
        """
        Save state variables.
        """
        for var in self._save_vars:
            self._stack.append(getattr(self, var))

    def pop_state(self):
        """
        Restore state variables.
        """
        for var in reversed(self._save_vars):
            setattr(self, var, self._stack.pop())

    def reset_state(self):
        """
        Reset internal state to initial values.
        """
        self.pop_state()
        self.push_state()

    def begin(self):
        """
        Set up projection transformations.
        """
        raise NotImplementedError('method not implemented')

    def end(self):
        """
        Tear down projection transformations.
        """
        raise NotImplementedError('method not implemented')

    def zoom(self, delta_x, delta_y):
        if delta_y > 0:
            self.zoom_factor = min(self.zoom_factor * 1.2, self.ZOOM_MAX)
        elif delta_y < 0:
            self.zoom_factor = max(self.zoom_factor * 0.83, self.ZOOM_MIN)


class ViewOrtho(ViewMode):
    """
    Orthographic projection transformations (2D mode).
    """
    NEAR       = -50.0
    FAR        =  50.0
    PAN_FACTOR =  4

    def __init__(self):
        super(ViewOrtho, self).__init__()

        self.x, self.y, self.z = 0.0, 0.0, 0.0
        self.zoom_factor       = 5.0
        self.azimuth           = 0.0
        self._save_vars.extend(['x', 'y', 'z', 'zoom_factor', 'azimuth'])
        self.push_state()

        self.w, self.h = None, None

    def begin(self, w, h):
        self.w, self.h = w, h
        glMatrixMode(GL_PROJECTION) # select projection matrix
        glPushMatrix()              # save the current projection matrix
        glLoadIdentity()            # set up orthographic projection
        glOrtho(0, w, 0, h, self.NEAR, self.FAR)
        glMatrixMode(GL_MODELVIEW)  # select the modelview matrix
        glPushMatrix()              # save the current modelview matrix
        glLoadIdentity()            # replace the modelview matrix with identity

    def end(self):
        """
        Switch back to perspective projection.
        """
        self.w, self.h = None, None
        # projection and modelview matrix stacks are separate, and can be
        # popped in any order
        glMatrixMode(GL_PROJECTION)
        glPopMatrix() # restore the projection matrix
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix() # restore the modelview matrix

    def display_transform(self):
        self._center_on_origin()
        glTranslate(self.x, self.y, self.z)
        glRotate(self.azimuth, 0.0, 0.0, 1.0)
        glScale(self.zoom_factor, self.zoom_factor, self.zoom_factor)

    def _center_on_origin(self):
        """
        Center orthographic projection box on (0, 0, 0).
        """
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        x, y = self.w / 2, self.h / 2
        glOrtho(-x, x, -y, y, self.NEAR, self.FAR)
        glMatrixMode(GL_MODELVIEW)

    def ui_transform(self, length):
        glTranslate(length + 20.0, length + 20.0, 0.0)
        glRotate(self.azimuth, 0.0, 0.0, 1.0)

    def rotate(self, delta_x, delta_y):
        self.azimuth += delta_x

    def pan(self, delta_x, delta_y):
        self.x += delta_x * self.PAN_FACTOR
        self.y -= delta_y * self.PAN_FACTOR


class ViewPerspective(ViewMode):
    """
    Perspective projection transformations (3D mode).
    """
    FOVY = 80.0
    NEAR = 0.1
    FAR  = 9000.0 # very far

    def __init__(self):
        super(ViewPerspective, self).__init__()

        self.x, self.y, self.z = 0.0, 180.0, -20.0
        self.zoom_factor = 1.0
        self.azimuth     = 0.0
        self.elevation   = -20.0
        self._save_vars.extend(['x', 'y', 'z', 'zoom_factor', 'azimuth', 'elevation'])
        self.push_state()

    def begin(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(self.FOVY, w / h, self.NEAR, self.FAR)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def end(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix() # restore the projection matrix
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix() # restore the modelview matrix

    def display_transform(self):
        glRotate(-90, 1.0, 0.0, 0.0) # make z point up
        glTranslate(0.0, self.y, 0.0)    # move away from the displayed object

        # zoom
        glScale(self.zoom_factor, self.zoom_factor, self.zoom_factor)

        # pan and rotate
        glTranslate(self.x, 0.0, self.z)
        glRotate(-self.elevation, 1.0, 0.0, 0.0)
        glRotate(self.azimuth, 0.0, 0.0, 1.0)

    def ui_transform(self, length):
        glRotate(-90, 1.0, 0.0, 0.0) # make z point up
        glTranslate(length + 20.0, 0.0, length + 20.0)
        glRotatef(-self.elevation, 1.0, 0.0, 0.0)
        glRotatef(self.azimuth, 0.0, 0.0, 1.0)

    def rotate(self, delta_x, delta_y):
        self.azimuth   += delta_x
        self.elevation -= delta_y

    def pan(self, delta_x, delta_y):
        self.x += delta_x / self.zoom_factor
        self.z -= delta_y / self.zoom_factor


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

        self.view_ortho = ViewOrtho()
        self.view_perspective = ViewPerspective()
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

    def load_file(self, model_file):
        self.model = model_file.load_model()
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

    # ------------------------------------------------------------------------
    # DRAWING
    # ------------------------------------------------------------------------

    def init(self):
        glClearColor(0.0, 0.0, 0.0, 0.0) # set clear color to black
        glClearDepth(1.0)                # set depth value to 1
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)

        # simulate translucency by blending colors
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glutInit()
        # TODO: doesn't this conflict with the constructor?
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)

        self.init_actors()
        self.initialized = True

    def init_actors(self):
        for actor in self.actors:
            if not actor.initialized:
                actor.init()

    def display(self, w, h):
        # clear the color and depth buffers from any leftover junk
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.view_ortho.begin(w, h)
        self.draw_axes()
        self.view_ortho.end()

        self.current_view.begin(w, h)
        self.current_view.display_transform()
        for actor in self.actors:
            actor.display(self.mode_2d)
        self.current_view.end()

        glFlush()

        # TODO: see if we have to enable any of these
        #glDepthMask(GL_TRUE)
        #glEnable(GL_DEPTH_TEST)
        #glEnable(GL_CULL_FACE)

    def reshape(self, w, h):
        glViewport(0, 0, w, h)

    def draw_axes(self, length=50.0):
        glPushMatrix()
        self.current_view.ui_transform(length)

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
            self.current_view.zoom(delta_x, delta_y)
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
        return isinstance(self.current_view, ViewOrtho)

    @mode_2d.setter
    def mode_2d(self, value):
        self.current_view = self.view_ortho if value else self.view_perspective

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


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
from gtk.gtkgl.apputils import GLScene, GLSceneButton, GLSceneButtonMotion

from .vector3 import Vector3


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


class Scene(GLScene, GLSceneButton, GLSceneButtonMotion):
    """
    A scene is responsible for displaying a model and accompanying objects (actors).

    In addition to calling display functions on its actors, the scene is also
    responsible for viewing transformations such as zooming, panning and
    rotation, as well as being the interface for the actors.
    """
    fovy   = 80.0
    z_near = 0.1
    z_far  = 9000.0 # very far

    def __init__(self):
        GLScene.__init__(self, gtk.gdkgl.MODE_RGB | gtk.gdkgl.MODE_DEPTH | gtk.gdkgl.MODE_DOUBLE)

        self.actors = []

        # 3D
        self.cursor_x = 0
        self.cursor_y = 0
        self.initial_obj_pos   = Vector3(0.0, 180.0, -20.0)
        self.initial_azimuth   = 0.0
        self.initial_elevation = -20.0
        self.reset_perspective() # set current viewing params

        # 2D
        self._mode_2d     = False
        self.ortho_near   = -50.0
        self.ortho_far    = 50.0
        self.initial_zoom_2d      = 5.0
        self.initial_obj_pos_x_2d = 0.0
        self.initial_obj_pos_y_2d = 0.0
        self.initial_azimuth_2d   = 0.0
        self.reset_ortho()

        self.initialized = False

        # dict of scene properties
        self._scene_properties = {
            'max_layers':     lambda: self.model.max_layers,
            'scaling-factor': lambda: round(self.model.scaling_factor, 2),
            'width':          lambda: self.model.width,
            'depth':          lambda: self.model.depth,
            'height':         lambda: self.model.height,
        }

    def set_model(self, model):
        self.model = model
        self.actors.append(model)

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
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)

        self.init_actors()
        self.initialized = True

    def init_actors(self):
        for actor in self.actors:
            if not actor.initialized:
                actor.init()

    def display(self, width, height):
        # clear the color and depth buffers from any leftover junk
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # replace current matrix with identity matrix
        glLoadIdentity()

        # TODO: see if we have to enable any of these
        #glDepthMask(GL_TRUE)
        #glEnable(GL_DEPTH_TEST)
        #glEnable(GL_CULL_FACE)

        self.switch_to_ortho(width, height)
        self.draw_axes()

        if self.mode_2d:
            # perform 2d transformations
            self.center_ortho_on_origin(width, height)
            glTranslate(self.obj_pos_x_2d, self.obj_pos_y_2d, 0)
            glRotate(self.azimuth_2d, 0.0, 0.0, 1.0)
            glScale(self.zoom_2d, self.zoom_2d, self.zoom_2d)
        else: # 3d
            # restore projection and modelview matrices and perform 3d
            # transformations
            self.restore_perspective()

            glRotate(-90, 1.0, 0.0, 0.0) # make z point up
            glTranslate(self.obj_pos.x, self.obj_pos.y, self.obj_pos.z)
            glRotate(-self.elevation, 1.0, 0.0, 0.0)
            glRotate(self.azimuth, 0.0, 0.0, 1.0)

        # draw actors
        for actor in self.actors:
            actor.display(self.mode_2d)

        # if mode is 2d, restore projection and modelview matrices
        if self.mode_2d:
            self.restore_perspective()

        glFlush()

    def reshape(self, width, height):
        glViewport(0, 0, width, height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fovy, width / height, self.z_near, self.z_far)
        glMatrixMode(GL_MODELVIEW)

    def switch_to_ortho(self, width, height):
        """
        Set up orthographic projection.
        """
        glMatrixMode(GL_PROJECTION) # select projection matrix
        glPushMatrix()              # save the current projection matrix
        glLoadIdentity()            # set up orthographic projection
        glOrtho(0, width, 0, height, self.ortho_near, self.ortho_far)
        glMatrixMode(GL_MODELVIEW)  # select the modelview matrix
        glPushMatrix()              # save the current modelview matrix
        glLoadIdentity()            # replace the modelview matrix with identity

    def center_ortho_on_origin(self, width, height):
        """
        Center orthographic projection box on (0, 0, 0).
        """
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        x, y = width / 2, height / 2
        glOrtho(-x, x, -y, y, self.ortho_near, self.ortho_far)
        glMatrixMode(GL_MODELVIEW)

    def restore_perspective(self):
        """
        Switch back to the perspective projection.
        """
        # projection and modelview matrix stacks are separate, so we don't have
        # to pop them in specific order
        glMatrixMode(GL_PROJECTION)
        glPopMatrix() # restore the projection matrix
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix() # restore the modelview matrix

    def draw_axes(self, length=50.0):
        glPushMatrix()

        if self.mode_2d:
            glTranslate(length + 20.0, length + 20.0, 0.0)
            glRotate(self.azimuth_2d, 0.0, 0.0, 1.0)
        else: # 3d
            glRotate(-90, 1.0, 0.0, 0.0) # make z point up
            glTranslatef(length + 20.0, 0.0, length + 20.0)
            glRotatef(-self.elevation, 1.0, 0.0, 0.0)
            glRotatef(self.azimuth, 0.0, 0.0, 1.0)

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
            self.rotate(event.x, event.y, delta_x, delta_y, width, height)
        elif event.state & gtk.gdk.BUTTON2_MASK: # middle mouse button
            self.zoom(delta_x, delta_y)
        elif event.state & gtk.gdk.BUTTON3_MASK: # right mouse button
            self.pan(delta_x, delta_y, width, height)

        self.cursor_x = event.x
        self.cursor_y = event.y

        self.invalidate()

    def reset_view(self, both=False):
        if both:
            self.reset_perspective()
            self.reset_ortho()
        elif self.mode_2d:
            self.reset_ortho()
        else: # 3d
            self.reset_perspective()

    def reset_perspective(self):
        self.obj_pos   = self.initial_obj_pos.copy()
        self.azimuth   = self.initial_azimuth
        self.elevation = self.initial_elevation

    def reset_ortho(self):
        self.obj_pos_x_2d = self.initial_obj_pos_x_2d
        self.obj_pos_y_2d = self.initial_obj_pos_y_2d
        self.azimuth_2d   = self.initial_azimuth_2d
        self.zoom_2d      = self.initial_zoom_2d

    def rotate(self, x, y, delta_x, delta_y, width, height):
        if self.mode_2d:
            self.azimuth_2d += delta_x / 4.0
        else: # 3d
            self.azimuth   += delta_x / 4.0
            self.elevation -= delta_y / 4.0

    def zoom(self, delta_x, delta_y):
        if self.mode_2d:
            zoom_2d = self.zoom_2d - (delta_y / 15.0)
            self.zoom_2d = max(zoom_2d, 0.1)
        else: # 3d
            self.obj_pos.y += delta_y / 10.0

    def pan(self, delta_x, delta_y, width, height):
        """
        Pan the model.

        Pannings works by relating mouse movements to movements in object
        space, using program window dimensions and field of view angle. A
        factor is applied to avoid speeding up on rapid mouse movements.
        """
        if self.mode_2d:
            self.obj_pos_x_2d += delta_x
            self.obj_pos_y_2d -= delta_y
        else: # 3d
            window_h = 2 * abs(self.obj_pos) * math.tan(self.fovy / 2) # height of window in object space

            magnitude_x = abs(delta_x)
            if magnitude_x > 0.0:
                x_scale = magnitude_x / width
                x_slow = 1 / magnitude_x
                offset_x = delta_x * x_scale * window_h * x_slow
                self.obj_pos.x -= offset_x

            magnitude_y = abs(delta_y)
            if magnitude_y > 0.0:
                y_scale = magnitude_y / width
                y_slow = 1 / magnitude_y
                offset_z = delta_y * y_scale * window_h * y_slow
                self.obj_pos.z += offset_z

    @property
    def mode_2d(self):
        return self._mode_2d

    @mode_2d.setter
    def mode_2d(self, value):
        self._mode_2d = value

    # ------------------------------------------------------------------------
    # MODEL MANIPULATION
    # ------------------------------------------------------------------------

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

    def rotate_model(self, angle, axis):
        self.model.rotate(angle, *axis)
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
        return self.model.modified


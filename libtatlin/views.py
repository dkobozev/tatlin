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


class ViewMode(object):
    """
    Base class for projection transformations.
    """
    ZOOM_MIN = 0.1
    ZOOM_MAX = 800

    def __init__(self):
        self._stack = []
        self._save_vars = []

        self.supports_ortho = False

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


class View2D(ViewMode):
    """
    Orthographic projection transformations (2D mode).
    """
    NEAR       = -100.0
    FAR        =  100.0
    PAN_FACTOR =  4

    def __init__(self):
        super(View2D, self).__init__()

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

    def zoom(self, delta_x, delta_y):
        old_zoom = self.zoom_factor
        super(View2D, self).zoom(delta_x, delta_y)

        # adjust panning for new zoom level
        self.x *= self.zoom_factor / old_zoom
        self.y *= self.zoom_factor / old_zoom


class View3D(ViewMode):
    """
    Perspective projection transformations (3D mode).
    """
    FOVY = 80.0
    ZOOM_ORTHO_ADJ = 4.5
    NEAR = 1
    FAR  = 100000

    def __init__(self):
        super(View3D, self).__init__()

        self.x, self.y, self.z = 0.0, 180.0, -20.0
        self.zoom_factor = 1.0
        self.azimuth     = 0.0
        self.elevation   = -20.0
        self.offset_x = self.offset_y = 0.0

        self.supports_ortho = True
        self.ortho          = False

        self._save_vars.extend(['x', 'y', 'z', 'zoom_factor', 'azimuth',
                                'elevation', 'offset_x', 'offset_y'])
        self.push_state()

    def begin(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        if self.ortho:
            x, y = w / 2, h / 2
            glOrtho(-x, x, -y, y, -self.FAR, self.FAR)
        else:
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
        glRotate(-90, 1.0, 0.0, 0.0)  # make z point up
        glTranslate(0.0, self.y, 0.0) # move away from the displayed object

        # zoom
        f = self.zoom_factor
        if self.ortho:
            # adjust zoom for orthographic projection in which the object's
            # distance from the camera has no effect on its apparent size
            f *= self.ZOOM_ORTHO_ADJ
        glScale(f, f, f)

        # pan and rotate
        glTranslate(self.x, 0.0, self.z)
        glRotate(-self.elevation, 1.0, 0.0, 0.0)
        glRotate(self.azimuth, 0.0, 0.0, 1.0)
        self._draw_rotation_center_bead()
        glTranslate(self.offset_x, self.offset_y, 0)

    def _draw_rotation_center_bead(self):
        glEnable(GL_LIGHTING)
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
        glLightfv(GL_LIGHT0, GL_POSITION, (20.0, 20.0, 20.0))
        glLightfv(GL_LIGHT1, GL_POSITION, (-20.0, -20.0, 20.0))

        glColor(1.0, 0.0, 0.0)
        glutSolidSphere(0.8, 100, 100)

        glDisable(GL_LIGHT1)
        glDisable(GL_LIGHT0)
        glDisable(GL_LIGHTING)

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

    def offset(self, delta_x, delta_y):
        self.offset_x += delta_x / self.zoom_factor
        self.offset_y -= delta_y / self.zoom_factor

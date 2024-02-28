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

from OpenGL.GL import *  # type:ignore
from OpenGL.GLE import *  # type:ignore

from .util import compile_display_list


class Platform(object):
    """
    Platform on which models are placed.
    """

    graduations_major = 10

    def __init__(self, width, depth):
        self.width = width
        self.depth = depth

        self.color_grads_minor = (0xAF / 255, 0xDF / 255, 0x5F / 255, 0.1)
        self.color_grads_interm = (0xAF / 255, 0xDF / 255, 0x5F / 255, 0.2)
        self.color_grads_major = (0xAF / 255, 0xDF / 255, 0x5F / 255, 0.33)
        self.color_fill = (0xAF / 255, 0xDF / 255, 0x5F / 255, 0.05)

        self.initialized = False

    def init(self):
        self.display_list = compile_display_list(self.draw)
        self.initialized = True

    def draw(self):
        glPushMatrix()

        glTranslate(-self.width / 2, -self.depth / 2, 0)

        def color(i):
            if i % self.graduations_major == 0:
                glColor(*self.color_grads_major)
            elif i % (self.graduations_major / 2) == 0:
                glColor(*self.color_grads_interm)
            else:
                glColor(*self.color_grads_minor)

        # draw the grid
        glBegin(GL_LINES)
        for i in range(0, int(self.width) + 1):
            color(i)
            glVertex3f(float(i), 0.0, 0.0)
            glVertex3f(float(i), self.depth, 0.0)

        for i in range(0, int(self.depth) + 1):
            color(i)
            glVertex3f(0, float(i), 0.0)
            glVertex3f(self.width, float(i), 0.0)
        glEnd()

        # draw fill
        glColor(*self.color_fill)
        glRectf(0.0, 0.0, self.width, self.depth)

        glPopMatrix()

    def display(self, *args, **kwargs):
        glCallList(self.display_list)

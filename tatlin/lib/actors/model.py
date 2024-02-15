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
import numpy

from .bounding_box import BoundingBox


class Model(object):
    """
    Parent class for models that provides common functionality.
    """

    AXIS_X = (1, 0, 0)
    AXIS_Y = (0, 1, 0)
    AXIS_Z = (0, 0, 1)

    letter_axis_map = {
        "x": AXIS_X,
        "y": AXIS_Y,
        "z": AXIS_Z,
    }

    axis_letter_map = dict([(v, k) for k, v in list(letter_axis_map.items())])

    def __init__(self, offset_x=0, offset_y=0, offset_z=0):
        self.vertices: numpy.ndarray

        self.offset_x = offset_x
        self.offset_y = offset_y
        self.offset_z = offset_z

        self.init_model_attributes()

    def init_model_attributes(self):
        """
        Set/reset saved properties.
        """
        self.invalidate_bounding_box()
        self.modified = False

    def invalidate_bounding_box(self):
        self._bounding_box = None

    @property
    def bounding_box(self):
        """
        Get a bounding box for the model.
        """
        if self._bounding_box is None:
            self._bounding_box = self._calculate_bounding_box()
        return self._bounding_box

    def _calculate_bounding_box(self):
        """
        Calculate an axis-aligned box enclosing the model.
        """
        # swap rows and columns in our vertex arrays so that we can do max and
        # min on axis 1
        xyz_rows = self.vertices.reshape(-1, order="F").reshape(3, -1)
        lower_corner = xyz_rows.min(1)
        upper_corner = xyz_rows.max(1)
        box = BoundingBox(upper_corner, lower_corner)
        return box

    @property
    def width(self):
        return self.bounding_box.width

    @property
    def depth(self):
        return self.bounding_box.depth

    @property
    def height(self):
        return self.bounding_box.height

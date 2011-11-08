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

import numpy
import math


identity_matrix = [
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
]

rotation_matrix_cache = {}

def translate(vertices, x, y, z):
    translated = vertices + numpy.array([x, y, z], 'f')
    return translated

def rotate(vertices, angle, x, y, z):
    key = (angle, x, y, z)
    if key not in rotation_matrix_cache:
        angle_r = math.radians(angle)
        c = math.cos(angle_r)
        s = math.sin(angle_r)
        C = 1 - c
        matrix = numpy.require([
            [x ** 2 * C + c,    x * y * C - z * s, x * z * C + y * s],
            [y * x * C + z * s, y ** 2 * C + c,    y * z * C - x * s],
            [x * z * C - y * s, y * z * C + x * s, z ** 2 * C + c],
        ], 'f')
        rotation_matrix_cache[key] = matrix

    matrix = rotation_matrix_cache[key]
    rotated = vertices.dot(matrix)
    return rotated


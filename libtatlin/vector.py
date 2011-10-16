from __future__ import division

import numpy
import math


identity_matrix = [
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
]

def translate(vertices, x, y, z):
    return vertices + numpy.require([x, y, z], 'f')

def rotate(vertices, angle, x, y, z):
    c = math.cos(angle)
    s = math.sin(angle)
    C = 1 - c
    matrix = numpy.require([
        [x ** 2 * C + c,    x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, y ** 2 * C + c,    y * z * C - x * s],
        [x * z * C - y * s, y * z * C + x * s, z ** 2 * C + c],
    ], 'f')
    return vertices.dot(matrix)


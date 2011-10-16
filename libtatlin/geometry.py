from __future__ import division

import math

def line_slope(ax, ay, bx, by):
    """
    Calculate slope of line AB.
    """
    slope = (by - ay) / (bx - ax)
    return slope

def points_angle(ax, ay, bx, by):
    """
    Calculate angle in degrees of line AB.
    """
    try:
        slope = line_slope(ax, ay, bx, by)
        angle = math.degrees(math.atan(slope))
        if bx > ax:
            angle = 180 + angle
    except ZeroDivisionError:
        angle = 90
        if by > ay:
            angle = 180 + angle

    return angle

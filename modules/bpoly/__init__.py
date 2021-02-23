import bpy

from .clearance import *
from .offset import *


if __name__ == "__main__":
    obj = bpy.context.active_object
    # vertices = [i.co.xyz for i in obj.data.splines[0].points]
    # offset_splines(obj.data.splines, distance=.2, add_screen=True)
    # offset_spline(obj.data.splines[0], distance=-.2, add_screen=True)
    # offset_2d(obj.data.splines[0], distance=.2, add_screen=True)
    # clearance_offset_splines(obj.data.splines, .2, add_screen=True)
    clearance_zigzag(obj.data.splines, distance=.2,  add_screen=True)

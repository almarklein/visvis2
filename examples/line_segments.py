"""
Display line segments. Can be useful e.g. for visializing vector fields.
"""

import numpy as np

import pygfx as gfx

from PyQt5 import QtWidgets
from wgpu.gui.qt import WgpuCanvas

app = QtWidgets.QApplication([])

canvas = WgpuCanvas()
renderer = gfx.WgpuRenderer(canvas)

scene = gfx.Scene()

x = np.linspace(20, 620, 200, dtype=np.float32)
y = np.sin(x / 10) * 100 + 200

positions = np.column_stack([x, y, np.zeros_like(x), np.ones_like(x)])
geometry = gfx.Geometry(positions=positions)

# Also see LineSegmentMaterial
material = gfx.LineArrowMaterial(thickness=6.0, color=(0.0, 0.7, 0.3, 0.5))
line = gfx.Line(geometry, material)
scene.add(line)

camera = gfx.ScreenCoordsCamera()


def animate():
    # would prefer to do this in a resize event only
    lsize = canvas.get_logical_size()
    camera.set_viewport_size(*lsize)
    renderer.render(scene, camera)
    canvas.request_draw()


if __name__ == "__main__":
    canvas.draw_frame = animate
    app.exec_()
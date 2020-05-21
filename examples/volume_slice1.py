"""
Render slices through a volume, by uploading to a 2D texture.
Simple and ... slow.
"""

import imageio
import visvis2 as vv

from PyQt5 import QtWidgets
from wgpu.gui.qt import WgpuCanvas


class WgpuCanvasWithScroll(WgpuCanvas):
    def wheelEvent(self, event):  # noqa: N802
        degrees = event.angleDelta().y() / 8
        scroll(degrees)


app = QtWidgets.QApplication([])

canvas = WgpuCanvasWithScroll()
renderer = vv.renderers.WgpuRenderer(canvas)
scene = vv.Scene()

vol = imageio.volread("imageio:stent.npz")
nslices = vol.shape[0]
index = nslices // 3
im = vol[index].copy()

tex = vv.Texture(im, dim=2, usage="sampled")

geometry = vv.PlaneGeometry(200, 200, 12, 12)
material = vv.MeshBasicMaterial(map=tex.get_view(filter="nearest"), clim=(0, 255))
plane = vv.Mesh(geometry, material)
plane.scale.y = -1
scene.add(plane)

fov, aspect, near, far = 70, -16 / 9, 1, 1000
camera = vv.PerspectiveCamera(fov, aspect, near, far)
camera.position.z = 200


def scroll(degrees):
    global index
    index = index + int(degrees / 15)
    index = max(0, min(nslices - 1, index))
    im = vol[index]
    tex.data[:] = im
    tex.update_range((0, 0, 0), tex.size)
    material.dirty = 1
    canvas.request_draw()


def animate():
    global t

    # would prefer to do this in a resize event only
    physical_size = canvas.get_physical_size()
    camera.set_viewport_size(*physical_size)

    # actually render the scene
    renderer.render(scene, camera)


if __name__ == "__main__":
    canvas.draw_frame = animate
    app.exec_()

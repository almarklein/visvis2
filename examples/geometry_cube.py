import numpy as np
import imageio
import visvis2 as vv

from PyQt5 import QtWidgets
from wgpu.gui.qt import WgpuCanvas


app = QtWidgets.QApplication([])

canvas = WgpuCanvas()
renderer = vv.renderers.WgpuRenderer(canvas)
scene = vv.Scene()

im = imageio.imread("imageio:chelsea.png")[:, :, :]
im = np.concatenate([im, 255 * np.ones(im.shape[:2] + (1,), dtype=im.dtype)], 2)
tex = vv.Texture(im, dim=2, usage="sampled").get_view(filter="linear")

geometry = vv.BoxGeometry(200, 200, 200)
material = vv.MeshBasicMaterial(map=tex, clim=(100, 255))
cube = vv.Mesh(geometry, material)
scene.add(cube)

fov, aspect, near, far = 70, 16 / 9, 1, 1000
camera = vv.PerspectiveCamera(fov, aspect, near, far)
camera.position.z = 400


def animate():
    # would prefer to do this in a resize event only
    physical_size = canvas.get_physical_size()
    camera.set_viewport_size(*physical_size)

    # cube.rotation.x += 0.005
    # cube.rotation.y += 0.01
    rot = vv.linalg.Quaternion().set_from_euler(vv.linalg.Euler(0.0005, 0.001))
    cube.rotation.multiply(rot)

    # actually render the scene
    renderer.render(scene, camera)

    # Request new frame
    canvas.request_draw()


if __name__ == "__main__":
    canvas.draw_frame = animate
    app.exec_()

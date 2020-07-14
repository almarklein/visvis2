"""
Render slices through a volume, by creating a 3D texture, and sample it in the shader.
Simple, fast and subpixel!
"""

import imageio
import numpy as np
import pygfx as gfx

from PyQt5 import QtWidgets
from wgpu.gui.qt import WgpuCanvas


app = QtWidgets.QApplication([])

canvas = WgpuCanvas()
renderer = gfx.renderers.WgpuRenderer(canvas)
scene = gfx.Scene()

background = gfx.Background(gfx.BackgroundMaterial((0, 1, 0, 1), (0, 1, 1, 1)))
scene.add(background)

scene.add(gfx.AxesHelper(size=10))

vol = imageio.volread("imageio:stent.npz")
tex = gfx.Texture(vol, dim=3, usage="sampled")
view = tex.get_view(filter="linear")

for axis in [0, 1, 2]:
    nslices = vol.shape[0]

    # TODO: if we could set the slicing plane on the material parametrically
    # we could reuse the same plane geometry for all slices here
    geometry = gfx.PlaneGeometry(200, 200, 1, 1)
    if axis == 0:  # YZ plane
        texcoords = np.array([
            [0.5, 0., 0],
            [0.5, 1., 0],
            [0.5, 0., nslices],
            [0.5, 1., nslices],
        ], dtype=np.float32)
    elif axis == 1:  # XZ plane
        texcoords = np.array([
            [0., 0.5, 0],
            [1., 0.5, 0],
            [0., 0.5, nslices],
            [1., 0.5, nslices],
        ], dtype=np.float32)
    elif axis == 2:  # XY plane (default)
        z_idx = nslices / 2
        texcoords = np.array([
            [0., 0., z_idx],
            [1., 0., z_idx],
            [0., 1., z_idx],
            [1., 1., z_idx],
        ], dtype=np.float32)
    print(texcoords)
    geometry.texcoords = gfx.Buffer(texcoords, usage="vertex|storage")

    material = gfx.MeshVolumeSliceMaterial(map=view, clim=(0, 255))
    plane = gfx.Mesh(geometry, material)

    # by default the plane is in XY plane
    if axis == 0:  # YZ plane
        plane.rotation.set_from_axis_angle(gfx.linalg.Vector3(0, 1, 0), 0.5 * np.pi)
    elif axis == 1:  # XZ plane
        plane.rotation.set_from_axis_angle(gfx.linalg.Vector3(1, 0, 0), 0.5 * np.pi)
    scene.add(plane)

camera = gfx.OrthographicCamera(200, 200)
camera.position.set(50, 50, 50)
camera.look_at(gfx.linalg.Vector3())


def animate():
    # global index
    # index = index + degrees / 30
    # index = max(0, min(nslices - 1, index))
    # geometry.texcoords.data[:, 2] = index / nslices
    # geometry.texcoords.update_range(0, geometry.texcoords.nitems)
    # material.dirty = 1  # todo: we should not have to mark the *material* dirty!

    renderer.render(scene, camera)
    canvas.request_draw()


if __name__ == "__main__":
    canvas.request_draw(animate)
    app.exec_()
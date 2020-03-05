import random

from PyQt5 import QtWidgets
from wgpu.gui.qt import WgpuCanvas

import visvis2 as vv


class Main(QtWidgets.QWidget):
    def __init__(self):
        super().__init__(None)
        self.resize(640, 480)

        # Creat button and hook it up
        self._button = QtWidgets.QPushButton("Add a line", self)
        self._button.clicked.connect(self._on_button_click)

        # Create canvas, renderer and a scene object
        self._canvas = WgpuCanvas(parent=self)
        self._renderer = vv.WgpuRenderer(self._canvas)
        self._scene = vv.Scene()
        self._camera = vv.ScreenCoordsCamera()

        # Hook up the animate callback
        self._canvas.draw_frame = self.animate

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self._button)
        layout.addWidget(self._canvas)

    def _on_button_click(self):
        positions = [
            [random.uniform(0, 400), random.uniform(0, 400), 0, 1] for i in range(8)
        ]
        line = vv.Line(vv.Geometry(positions=positions), vv.LineStripMaterial())
        self._scene.add(line)
        self._canvas.update()

    def animate(self):
        width, height, ratio = self._canvas.get_size_and_pixel_ratio()
        self._camera.set_viewport_size(width, height)
        self._renderer.render(self._scene, self._camera)


app = QtWidgets.QApplication([])
m = Main()
m.show()


if __name__ == "__main__":
    app.exec_()

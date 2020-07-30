from ._base import Camera
from ..linalg import Matrix4


class OrthographicCamera(Camera):
    """ An orthographic camera, useful for non-perspective views and
    visualizing 2D content. You may also want to set the position of
    the camera.

    Parameters:
        width (float): The (minimum) width of the view-cube. The actual view
           may be wider if the viewport is wide.
        height (float): The (minimum) height of the view-cube.
        near (float): The near clipping plane. Default -1000.
        far (float): The far clipping plane. Must be larger than near. Default +1000.
    """

    def __init__(self, width=1, height=1, near=-1000, far=1000):
        super().__init__()
        self.near = float(near)
        self.far = float(far)
        assert self.near < self.far
        self.zoom = 1
        self._maintain_aspect = True
        self.set_viewport_size(width, height)
        self.update_projection_matrix()

    def __repr__(self) -> str:
        return (
            f"OrthographicCamera({self.width}, {self.height}, {self.near}, {self.far})"
        )

    def set_viewport_size(self, width, height):
        self.width = float(width)
        self.height = float(height)
        width = self.width / self.zoom
        height = self.height / self.zoom
        # Calculate bounds
        self.top = +0.5 * height
        self.bottom = -0.5 * height
        self.left = -0.5 * width
        self.right = +0.5 * width

    def update_projection_matrix(self):
        # Set matrices
        # The linalg ortho projection puts xyz in the range -1..1, but
        # in the coordinate system of wgpu (and this lib) the depth is
        # expressed in 0..1, so we also correct for that.
        self.projection_matrix.make_orthographic(
            self.left, self.right, self.top, self.bottom, self.near, self.far
        )
        self.projection_matrix.premultiply(
            Matrix4(1, 0, 0.0, 0, 0, 1, 0.0, 0, 0.0, 0.0, 0.5, 0.0, 0, 0, 0.5, 1)
        )
        self.projection_matrix_inverse.get_inverse(self.projection_matrix)

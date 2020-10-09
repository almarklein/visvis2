import wgpu  # only for flags/enums
import pyshader
from pyshader import python2shader
from pyshader import i32, vec2, vec4, Struct

from ...utils import array_from_shadertype


class RenderTexture:
    """Class used internally to store a render texture and meta data."""

    def __init__(self, format):
        self.format = format
        self.texture = None
        self.texture_view = None
        self.size = (0, 0, 0)

    def set_texture_view(self, texture_view):
        """Set from a texture view. Intended when the texture comes
        from elsewhere. Make sure it matches the format!
        """
        self.texture = None
        self.texture_view = texture_view
        self.size = self.texture_view.size

    def ensure_size(self, device, size):
        """Make sure that the texture has the given size. If necessary,
        recreates the texture and texture-view objects.
        """
        if size != self.size:
            self.size = size
            usage = wgpu.TextureUsage.OUTPUT_ATTACHMENT | wgpu.TextureUsage.COPY_SRC
            if self.format.startswith(("rgb", "bgr")):
                usage |= wgpu.TextureUsage.SAMPLED
            self.texture = device.create_texture(
                size=size, usage=usage, dimension="2d", format=self.format
            )
            self.texture_view = self.texture.create_view()


def render_full_screen_texture(
    device, render_texture_src, render_texture_dst, wgpu_sampler
):
    """Render one texture to another."""

    uniform_data = array_from_shadertype(texture_render_uniform_type)
    uniform_data["size"] = render_texture_src.size[:2]
    # todo: Gaussian function for aa kernel
    uniform_data["kernel"] = 1, 1, 0, 0
    uniform_data["support"] = 2

    uniforms = device.create_buffer_with_data(
        data=uniform_data,
        usage=wgpu.BufferUsage.UNIFORM,
    )

    binding_layouts = [
        {
            "binding": 0,
            "visibility": wgpu.ShaderStage.FRAGMENT,
            "type": wgpu.BindingType.sampler,
        },
        {
            "binding": 1,
            "visibility": wgpu.ShaderStage.FRAGMENT,
            "type": wgpu.BindingType.sampled_texture,
            "view_dimension": wgpu.TextureViewDimension.d2,
            "texture_component_type": wgpu.TextureComponentType.float,
            "multisampled": False,
        },
        {
            "binding": 2,
            "visibility": wgpu.ShaderStage.FRAGMENT,
            "type": wgpu.BindingType.uniform_buffer,
        },
    ]
    bindings = [
        {"binding": 0, "resource": wgpu_sampler},
        {"binding": 1, "resource": render_texture_src.texture_view},
        {
            "binding": 2,
            "resource": {"buffer": uniforms, "offset": 0, "size": uniform_data.nbytes},
        },
    ]

    bind_group_layout = device.create_bind_group_layout(entries=binding_layouts)
    pipeline_layout = device.create_pipeline_layout(
        bind_group_layouts=[bind_group_layout]
    )
    bind_group = device.create_bind_group(layout=bind_group_layout, entries=bindings)

    vs_module = device.create_shader_module(code=vertex_shader)
    fs_module = device.create_shader_module(code=fragment_shader)

    final_render_pipeline = device.create_render_pipeline(
        layout=pipeline_layout,
        vertex_stage={"module": vs_module, "entry_point": "main"},
        fragment_stage={"module": fs_module, "entry_point": "main"},
        primitive_topology=wgpu.PrimitiveTopology.triangle_strip,
        color_states=[
            {
                "format": render_texture_dst.format,
                "alpha_blend": (
                    wgpu.BlendFactor.one,
                    wgpu.BlendFactor.zero,
                    wgpu.BlendOperation.add,
                ),
                "color_blend": (
                    wgpu.BlendFactor.src_alpha,
                    wgpu.BlendFactor.one_minus_src_alpha,
                    wgpu.BlendOperation.add,
                ),
            }
        ],
        vertex_state={
            "index_format": wgpu.IndexFormat.uint32,
            "vertex_buffers": [],
        },
    )
    #
    command_encoder = device.create_command_encoder()  # todo: reuse command encoder?
    render_pass = command_encoder.begin_render_pass(
        color_attachments=[
            {
                "attachment": render_texture_dst.texture_view,
                "resolve_target": None,
                "load_value": (0, 0, 0, 0),  # LoadOp.load or color
                "store_op": wgpu.StoreOp.store,
            }
        ],
        depth_stencil_attachment=None,
        occlusion_query_set=None,
    )
    render_pass.set_pipeline(final_render_pipeline)
    render_pass.set_bind_group(0, bind_group, [], 0, 99)
    render_pass.draw(4, 1)
    render_pass.end_pass()
    device.default_queue.submit([command_encoder.finish()])


# %% Shaders


texture_render_uniform_type = Struct(kernel=vec4, size=vec2, support=i32)


@python2shader
def vertex_shader(
    index: (pyshader.RES_INPUT, "VertexId", "i32"),
    out_pos: (pyshader.RES_OUTPUT, "Position", vec4),
    v_texcoord: (pyshader.RES_OUTPUT, 0, vec2),
):
    positions = [vec2(0, 1), vec2(0, 0), vec2(1, 1), vec2(1, 0)]
    pos = positions[index]
    v_texcoord = pos  # noqa - shader output
    out_pos = vec4(pos * 2.0 - 1.0, 0.0, 1.0)  # noqa - shader output


@python2shader
def fragment_shader(
    v_texcoord: (pyshader.RES_INPUT, 0, vec2),
    s_sam: (pyshader.RES_SAMPLER, (0, 0), ""),
    t_tex: (pyshader.RES_TEXTURE, (0, 1), "2d f32"),
    u_render: (pyshader.RES_UNIFORM, (0, 2), texture_render_uniform_type),
    out_color: (pyshader.RES_OUTPUT, 0, vec4),
):

    step = vec2(1.0 / u_render.size.x, 1.0 / u_render.size.y)
    kernel = [
        u_render.kernel.x,
        u_render.kernel.y,
        u_render.kernel.z,
        u_render.kernel.w,
    ]
    support = min(3, u_render.support)

    val = vec4(0.0, 0.0, 0.0, 0.0)
    weight = 0.0
    for y in range(-support, support + 1):
        for x in range(-support, support + 1):
            texcoord = v_texcoord + vec2(x, y) * step
            w = kernel[abs(x)] * kernel[abs(y)]
            val += t_tex.sample(s_sam, texcoord) * w
            weight += w

    out_color = val / weight  # noqa - shader output

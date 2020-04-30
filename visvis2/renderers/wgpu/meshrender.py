import wgpu  # only for flags/enums
import python_shader
from python_shader import vec2, vec4

from . import register_wgpu_render_function, stdinfo_uniform_type
from ...objects import Mesh
from ...materials._mesh_basic import uniform_type, MeshBasicMaterial
from ...datawrappers import BaseBuffer, BaseTexture, TextureView


@python_shader.python2shader
def vertex_shader(
    in_pos: (python_shader.RES_INPUT, 0, vec4),
    in_texcoord: (python_shader.RES_INPUT, 1, vec2),
    out_pos: (python_shader.RES_OUTPUT, "Position", vec4),
    v_texcoord: (python_shader.RES_OUTPUT, 0, vec2),
    u_stdinfo: (python_shader.RES_UNIFORM, (0, 0), stdinfo_uniform_type),
):
    world_pos = u_stdinfo.world_transform * vec4(in_pos.xyz, 1.0)
    ndc_pos = u_stdinfo.projection_transform * u_stdinfo.cam_transform * world_pos

    out_pos = ndc_pos  # noqa - shader output
    v_texcoord = in_texcoord  # noqa - shader output


@python_shader.python2shader
def fragment_shader_simple(
    u_mesh: (python_shader.RES_UNIFORM, (1, 0), uniform_type),
    out_color: (python_shader.RES_OUTPUT, 0, vec4),
):
    out_color = u_mesh.color  # noqa - shader output


@python_shader.python2shader
def fragment_shader_textured_gray(
    v_texcoord: (python_shader.RES_INPUT, 0, vec2),
    u_mesh: (python_shader.RES_UNIFORM, (1, 0), uniform_type),
    s_sam: (python_shader.RES_SAMPLER, (1, 1), ""),
    t_tex: (python_shader.RES_TEXTURE, (1, 2), "2d i32"),
    out_color: (python_shader.RES_OUTPUT, 0, vec4),
):
    val = f32(t_tex.sample(s_sam, v_texcoord).r)
    val = (val - u_mesh.clim[0]) / (u_mesh.clim[1] - u_mesh.clim[0])
    out_color = vec4(val, val, val, 1.0)  # noqa - shader output


@python_shader.python2shader
def fragment_shader_textured_rgba(
    v_texcoord: (python_shader.RES_INPUT, 0, vec2),
    u_mesh: (python_shader.RES_UNIFORM, (1, 0), uniform_type),
    s_sam: (python_shader.RES_SAMPLER, (1, 1), ""),
    t_tex: (python_shader.RES_TEXTURE, (1, 2), "2d i32"),
    out_color: (python_shader.RES_OUTPUT, 0, vec4),
):
    color = vec4(t_tex.sample(s_sam, v_texcoord))
    color = (color - u_mesh.clim[0]) / (u_mesh.clim[1] - u_mesh.clim[0])
    out_color = color  # noqa - shader output


@register_wgpu_render_function(Mesh, MeshBasicMaterial)
def mesh_renderer(wobject, render_info):
    """ Render function capable of rendering meshes.
    """

    geometry = wobject.geometry
    material = wobject.material  # noqa

    # Get stuff from material

    # ...

    # Get stuff from geometry

    fragment_shader = fragment_shader_simple

    # Use index buffer if present on the geometry
    index_buffer = getattr(geometry, "index", None)
    index_buffer = index_buffer if isinstance(index_buffer, BaseBuffer) else None

    # Collect vertex buffers
    # todo: must vetex_buffers be a dict?
    vertex_buffers = []
    vertex_buffers.append(geometry.positions)
    if getattr(geometry, "texcoords", None) is not None:
        vertex_buffers.append(geometry.texcoords)

    bindings0 = {0: (wgpu.BindingType.uniform_buffer, render_info.stdinfo)}
    bindings1 = {}

    bindings1[0] = wgpu.BindingType.uniform_buffer, material.uniform_buffer

    # Collect texture and sampler
    if material.map is not None:
        if isinstance(material.map, BaseTexture):
            raise TypeError("material.map is a Texture, but must be a TextureView")
        elif not isinstance(material.map, TextureView):
            raise TypeError("material.map must be a TextureView")
        elif getattr(geometry, "texcoords", None) is None:
            raise ValueError("material.map is present, but geometry has no texcoords")
        bindings1[1] = wgpu.BindingType.sampler, material.map
        bindings1[2] = wgpu.BindingType.sampled_texture, material.map
        if "rgba" in material.map.format:
            fragment_shader = fragment_shader_textured_rgba
        else:
            fragment_shader = fragment_shader_textured_gray

    if index_buffer:
        n = len(index_buffer.data)
    else:
        n = len(vertex_buffers[0].data)

    # Put it together!

    return [
        {
            "vertex_shader": vertex_shader,
            "fragment_shader": fragment_shader,
            "primitive_topology": wgpu.PrimitiveTopology.triangle_list,
            "indices": (range(n), range(1)),
            "index_buffer": index_buffer,
            "vertex_buffers": vertex_buffers,
            "bindings0": bindings0,
            "bindings1": bindings1,
        }
    ]

bl_info = {
    "name": "VRM Anime Shader - MToon to Anime Converter",
    "author": "opencode",
    "version": (2, 0, 3),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Anime Shader",
    "description": "Convert VRM MToon materials to anime-style EEVEE shaders with preset switching and scene-light integration",
    "category": "Material",
}

import bpy
from bpy.props import (
    EnumProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
)

# ============================================================
# CONSTANTS
# ============================================================

SHADER_GROUP_NAME = "VRM_AnimeShader"
SHADER_GROUP_LABEL = "VRM Anime Shader"
SHADER_VERSION = 3
GROUP_VERSION_KEY = "vas_version"

# Preset values.  Every key maps to a group interface socket except the
# per-material sockets (Base Color / Shade Color / Shade Texture / Emission
# Color / Alpha / Normal) which are wired during conversion.
PRESET_DEFAULTS = {
    "anime_clean": {
        "label": "Anime Clean",
        "shadow_color": (0.84, 0.80, 0.95, 1.0),
        "shadow_threshold": 0.50,
        "shadow_smoothness": 0.06,
        "shade_tint_strength": 0.20,
        "shift_influence": 0.35,
        "light_normalize": 3.0,
        "ambient_floor": 0.30,
        "light_response": 0.55,
        "light_tint": 0.30,
        "rim_color": (0.85, 0.88, 1.0, 1.0),
        "rim_strength": 0.12,
        "rim_threshold": 0.62,
        "specular_color": (1.0, 1.0, 1.0, 1.0),
        "specular_strength": 0.12,
        "specular_smoothness": 0.35,
        "saturation": 1.02,
        "brightness": 1.0,
        "emission_strength": 1.0,
    },
    "mtoon_faithful": {
        "label": "MToon Faithful",
        "shadow_color": (1.0, 1.0, 1.0, 1.0),
        "shadow_threshold": 0.50,
        "shadow_smoothness": 0.04,
        "shade_tint_strength": 0.0,
        "shift_influence": 1.0,
        "light_normalize": 3.0,
        "ambient_floor": 0.22,
        "light_response": 0.0,
        "light_tint": 0.0,
        "rim_color": (1.0, 1.0, 1.0, 1.0),
        "rim_strength": 0.0,
        "rim_threshold": 0.65,
        "specular_color": (1.0, 1.0, 1.0, 1.0),
        "specular_strength": 0.0,
        "specular_smoothness": 0.30,
        "saturation": 1.0,
        "brightness": 1.0,
        "emission_strength": 1.0,
    },
    "wuthering_waves": {
        "label": "Wuthering Waves",
        "shadow_color": (0.80, 0.82, 1.0, 1.0),
        "shadow_threshold": 0.46,
        "shadow_smoothness": 0.08,
        "shade_tint_strength": 0.35,
        "shift_influence": 0.28,
        "light_normalize": 2.6,
        "ambient_floor": 0.32,
        "light_response": 0.65,
        "light_tint": 0.40,
        "rim_color": (0.75, 0.85, 1.0, 1.0),
        "rim_strength": 0.22,
        "rim_threshold": 0.55,
        "specular_color": (0.95, 0.97, 1.0, 1.0),
        "specular_strength": 0.18,
        "specular_smoothness": 0.45,
        "saturation": 1.06,
        "brightness": 1.0,
        "emission_strength": 1.05,
    },
    "genshin_impact": {
        "label": "Genshin Impact",
        "shadow_color": (0.86, 0.82, 0.96, 1.0),
        "shadow_threshold": 0.52,
        "shadow_smoothness": 0.04,
        "shade_tint_strength": 0.25,
        "shift_influence": 0.40,
        "light_normalize": 3.2,
        "ambient_floor": 0.28,
        "light_response": 0.55,
        "light_tint": 0.25,
        "rim_color": (0.90, 0.90, 1.0, 1.0),
        "rim_strength": 0.15,
        "rim_threshold": 0.66,
        "specular_color": (1.0, 0.98, 0.95, 1.0),
        "specular_strength": 0.10,
        "specular_smoothness": 0.30,
        "saturation": 1.04,
        "brightness": 1.0,
        "emission_strength": 1.0,
    },
    "honkai_star": {
        "label": "Honkai Star Rail",
        "shadow_color": (0.80, 0.78, 0.98, 1.0),
        "shadow_threshold": 0.48,
        "shadow_smoothness": 0.06,
        "shade_tint_strength": 0.30,
        "shift_influence": 0.35,
        "light_normalize": 2.8,
        "ambient_floor": 0.30,
        "light_response": 0.60,
        "light_tint": 0.35,
        "rim_color": (0.78, 0.84, 1.0, 1.0),
        "rim_strength": 0.18,
        "rim_threshold": 0.58,
        "specular_color": (0.92, 0.94, 1.0, 1.0),
        "specular_strength": 0.15,
        "specular_smoothness": 0.40,
        "saturation": 1.05,
        "brightness": 1.0,
        "emission_strength": 1.0,
    },
    "flat_shade": {
        "label": "Flat Cel Shade",
        "shadow_color": (0.88, 0.86, 0.94, 1.0),
        "shadow_threshold": 0.55,
        "shadow_smoothness": 0.0,
        "shade_tint_strength": 0.15,
        "shift_influence": 0.45,
        "light_normalize": 3.0,
        "ambient_floor": 0.25,
        "light_response": 0.35,
        "light_tint": 0.10,
        "rim_color": (1.0, 1.0, 1.0, 1.0),
        "rim_strength": 0.0,
        "rim_threshold": 0.70,
        "specular_color": (1.0, 1.0, 1.0, 1.0),
        "specular_strength": 0.0,
        "specular_smoothness": 0.20,
        "saturation": 1.0,
        "brightness": 1.0,
        "emission_strength": 1.0,
    },
    "soft_anime": {
        "label": "Soft Anime",
        "shadow_color": (0.90, 0.86, 0.96, 1.0),
        "shadow_threshold": 0.52,
        "shadow_smoothness": 0.16,
        "shade_tint_strength": 0.20,
        "shift_influence": 0.40,
        "light_normalize": 3.0,
        "ambient_floor": 0.35,
        "light_response": 0.55,
        "light_tint": 0.25,
        "rim_color": (0.82, 0.86, 0.98, 1.0),
        "rim_strength": 0.12,
        "rim_threshold": 0.60,
        "specular_color": (1.0, 0.99, 0.97, 1.0),
        "specular_strength": 0.08,
        "specular_smoothness": 0.55,
        "saturation": 1.0,
        "brightness": 1.02,
        "emission_strength": 1.0,
    },
}

# Scene properties that are synchronised to every anime material.
SYNC_SOCKET_MAP = {
    "shadow_color": "Shadow Color",
    "shadow_threshold": "Shadow Threshold",
    "shadow_smoothness": "Shadow Smoothness",
    "shade_tint_strength": "Shade Tint Strength",
    "shift_influence": "Shift Influence",
    "light_normalize": "Light Normalize",
    "ambient_floor": "Ambient Floor",
    "light_response": "Light Response",
    "light_tint": "Light Tint",
    "rim_color": "Rim Color",
    "rim_strength": "Rim Strength",
    "rim_threshold": "Rim Threshold",
    "specular_color": "Specular Color",
    "specular_strength": "Specular Strength",
    "specular_smoothness": "Specular Smoothness",
    "saturation": "Saturation",
    "brightness": "Brightness",
    "emission_strength": "Emission Strength",
}

REQUIRED_INPUTS = {
    "Base Color",
    "Shade Color",
    "Shade Texture",
    "Shade Shift",
    "Shade Toony",
    "Shadow Color",
    "Shadow Threshold",
    "Shadow Smoothness",
    "Shade Tint Strength",
    "Light Normalize",
    "Ambient Floor",
    "Light Response",
    "Light Tint",
    "Rim Color",
    "Rim Strength",
    "Rim Threshold",
    "Specular Color",
    "Specular Strength",
    "Specular Smoothness",
    "Saturation",
    "Brightness",
    "Emission Color",
    "Emission Strength",
    "Alpha",
    "Normal",
}
REQUIRED_OUTPUTS = {"Surface"}


# ============================================================
# SHADER GROUP BUILDER (v2)
# ============================================================


def _new_socket(group, name, in_out, socket_type, **kwargs):
    """Create a socket on a ShaderNodeGroup interface (Blender 4.0+)."""
    sock = group.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
    for k, v in kwargs.items():
        setattr(sock, k, v)
    return sock


def ensure_anime_shader_group(context):
    """Create or get the anime shader node group. Rebuilds if stale."""
    existing = bpy.data.node_groups.get(SHADER_GROUP_NAME)
    if existing and existing.type == "SHADER":
        existing_inputs = {
            s.name
            for s in existing.interface.items_tree
            if s.item_type == "SOCKET" and s.in_out == "INPUT"
        }
        existing_outputs = {
            s.name
            for s in existing.interface.items_tree
            if s.item_type == "SOCKET" and s.in_out == "OUTPUT"
        }
        version_ok = existing.get(GROUP_VERSION_KEY) == SHADER_VERSION
        if (
            version_ok
            and REQUIRED_INPUTS.issubset(existing_inputs)
            and REQUIRED_OUTPUTS.issubset(existing_outputs)
        ):
            return existing
        bpy.data.node_groups.remove(existing)
    elif existing:
        bpy.data.node_groups.remove(existing)
    return _build_anime_shader_group(context)


def _build_anime_shader_group(context):
    """Build the complete anime shader node group from scratch."""
    group = bpy.data.node_groups.new(SHADER_GROUP_NAME, "ShaderNodeTree")
    group[GROUP_VERSION_KEY] = SHADER_VERSION
    group.description = "Toon shader driven by actual EEVEE scene lighting"

    # ---------------- interface ----------------
    _new_socket(group, "Base Color", "INPUT", "NodeSocketColor", default_value=(1, 1, 1, 1))
    _new_socket(group, "Shade Color", "INPUT", "NodeSocketColor", default_value=(1, 1, 1, 1))
    _new_socket(group, "Shade Texture", "INPUT", "NodeSocketColor", default_value=(1, 1, 1, 1))
    _new_socket(group, "Shade Shift", "INPUT", "NodeSocketFloat", default_value=0.0, min_value=-2.0, max_value=2.0)
    _new_socket(group, "Shade Toony", "INPUT", "NodeSocketFloat", default_value=0.9, min_value=0.0, max_value=1.0)
    _new_socket(group, "Shift Influence", "INPUT", "NodeSocketFloat", default_value=0.42, min_value=0.0, max_value=1.5, subtype="FACTOR")
    _new_socket(group, "Shadow Color", "INPUT", "NodeSocketColor", default_value=(0.84, 0.80, 0.95, 1.0))
    _new_socket(group, "Shadow Threshold", "INPUT", "NodeSocketFloat", default_value=0.50, min_value=0.0, max_value=1.0, subtype="FACTOR")
    _new_socket(group, "Shadow Smoothness", "INPUT", "NodeSocketFloat", default_value=0.05, min_value=0.0, max_value=0.5)
    _new_socket(group, "Shade Tint Strength", "INPUT", "NodeSocketFloat", default_value=0.20, min_value=0.0, max_value=1.0, subtype="FACTOR")
    _new_socket(group, "Light Normalize", "INPUT", "NodeSocketFloat", default_value=3.0, min_value=0.1, max_value=20.0)
    _new_socket(group, "Ambient Floor", "INPUT", "NodeSocketFloat", default_value=0.30, min_value=0.0, max_value=1.0, subtype="FACTOR")
    _new_socket(group, "Light Response", "INPUT", "NodeSocketFloat", default_value=0.60, min_value=0.0, max_value=1.0, subtype="FACTOR")
    _new_socket(group, "Light Tint", "INPUT", "NodeSocketFloat", default_value=0.30, min_value=0.0, max_value=1.0, subtype="FACTOR")
    _new_socket(group, "Rim Color", "INPUT", "NodeSocketColor", default_value=(0.85, 0.88, 1.0, 1.0))
    _new_socket(group, "Rim Strength", "INPUT", "NodeSocketFloat", default_value=0.12, min_value=0.0, max_value=2.0)
    _new_socket(group, "Rim Threshold", "INPUT", "NodeSocketFloat", default_value=0.62, min_value=0.0, max_value=1.0, subtype="FACTOR")
    _new_socket(group, "Specular Color", "INPUT", "NodeSocketColor", default_value=(1, 1, 1, 1))
    _new_socket(group, "Specular Strength", "INPUT", "NodeSocketFloat", default_value=0.12, min_value=0.0, max_value=2.0)
    _new_socket(group, "Specular Smoothness", "INPUT", "NodeSocketFloat", default_value=0.35, min_value=0.0, max_value=1.0)
    _new_socket(group, "Saturation", "INPUT", "NodeSocketFloat", default_value=1.02, min_value=0.0, max_value=3.0)
    _new_socket(group, "Brightness", "INPUT", "NodeSocketFloat", default_value=1.0, min_value=0.0, max_value=3.0)
    _new_socket(group, "Emission Color", "INPUT", "NodeSocketColor", default_value=(0, 0, 0, 1))
    _new_socket(group, "Emission Strength", "INPUT", "NodeSocketFloat", default_value=1.0, min_value=0.0, max_value=10.0)
    _new_socket(group, "Alpha", "INPUT", "NodeSocketFloat", default_value=1.0, min_value=0.0, max_value=1.0, subtype="FACTOR")
    _new_socket(group, "Normal", "INPUT", "NodeSocketVector", default_value=(0.0, 0.0, 1.0))
    _new_socket(group, "Surface", "OUTPUT", "NodeSocketShader")

    nodes = group.nodes
    links = group.links

    def N(n_type, label, loc):
        n = nodes.new(n_type)
        n.location = loc
        n.label = label
        return n

    def math_node(op, label, loc, a=None, b=None):
        n = N("ShaderNodeMath", label, loc)
        n.operation = op
        if a is not None:
            if isinstance(a, (int, float)):
                n.inputs[0].default_value = a
            else:
                links.new(a, n.inputs[0])
        if b is not None:
            if isinstance(b, (int, float)):
                n.inputs[1].default_value = b
            else:
                links.new(b, n.inputs[1])
        return n

    def mix_rgb(blend, label, loc):
        n = N("ShaderNodeMixRGB", label, loc)
        n.blend_type = blend
        n.inputs[0].default_value = 1.0
        return n

    def link(sock_out, sock_in):
        links.new(sock_out, sock_in)

    n_in = N("NodeGroupInput", "Group Input", (-2100, 0))
    n_out = N("NodeGroupOutput", "Group Output", (1600, 0))

    # ---------------- scene light probes ----------------
    # A white diffuse probe sampled through Shader-to-RGB gives the actual
    # EEVEE irradiance (sun, sky/world, area lights, coloured lights, shadows).
    # The probe uses the geometric normal so painted normal maps do not create
    # noisy toon patches on cheeks; the normal map is reserved for specular.
    geo = N("ShaderNodeNewGeometry", "Geometry", (-2100, 900))
    diffuse = N("ShaderNodeBsdfDiffuse", "Light Probe", (-1900, 800))
    diffuse.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    link(geo.outputs["Normal"], diffuse.inputs["Normal"])
    s2rgb = N("ShaderNodeShaderToRGB", "Light to RGB", (-1700, 800))
    link(diffuse.outputs[0], s2rgb.inputs[0])

    dot = N("ShaderNodeVectorMath", "Light Luma", (-1500, 820))
    dot.operation = "DOT_PRODUCT"
    link(s2rgb.outputs["Color"], dot.inputs[0])
    dot.inputs[1].default_value = (0.2126, 0.7152, 0.0722)

    luma_safe = math_node("MAXIMUM", "Luma Safe", (-1500, 620), dot.outputs["Value"], 0.001)

    # chroma = iridescence / luma  (normalised light colour)
    combine = N("ShaderNodeCombineXYZ", "Luma Vec", (-1500, 470))
    for k in ("X", "Y", "Z"):
        link(luma_safe.outputs[0], combine.inputs[k])
    chroma = N("ShaderNodeVectorMath", "Light Chroma", (-1300, 620))
    chroma.operation = "DIVIDE"
    link(s2rgb.outputs["Color"], chroma.inputs[0])
    link(combine.outputs[0], chroma.inputs[1])

    # x = luma / (luma + k)  -> scene-independent 0..1 light level
    add_k = math_node("ADD", "Luma + K", (-1300, 820), dot.outputs["Value"], n_in.outputs["Light Normalize"])
    div_x = math_node("DIVIDE", "Normalise Light", (-1150, 820), dot.outputs["Value"], add_k.outputs[0])
    x_clamped = N("ShaderNodeClamp", "Light Level", (-1000, 820))
    x_clamped.inputs["Min"].default_value = 0.0
    x_clamped.inputs["Max"].default_value = 1.0
    link(div_x.outputs[0], x_clamped.inputs["Value"])

    # ---------------- toon threshold ----------------
    # MToon's per-material Shading Shift/Toony are preserved so that a model
    # authored as "almost fully lit" (shift ~= 1) stays that way, while models
    # with shift ~= 0 get a proper two-tone terminator.
    toony_scale = math_node("MULTIPLY", "Toony Scale", (-1500, 260), n_in.outputs["Shade Toony"], 0.8)
    toony_soft = math_node("SUBTRACT", "Toony Softness", (-1350, 260), 1.0, toony_scale.outputs[0])
    smooth_raw = math_node("MULTIPLY", "Smoothness x Toony", (-1200, 300), n_in.outputs["Shadow Smoothness"], toony_soft.outputs[0])
    smooth = math_node("MAXIMUM", "Smooth Safe", (-1050, 300), smooth_raw.outputs[0], 0.002)
    shift_term = math_node("MULTIPLY", "MToon Shift", (-1350, 120), n_in.outputs["Shade Shift"], n_in.outputs["Shift Influence"])
    thresh = math_node("SUBTRACT", "Effective Threshold", (-1150, 160), n_in.outputs["Shadow Threshold"], shift_term.outputs[0])
    low = math_node("SUBTRACT", "Threshold Low", (-1000, 200), thresh.outputs[0], smooth.outputs[0])
    high = math_node("ADD", "Threshold High", (-1000, 100), thresh.outputs[0], smooth.outputs[0])
    toon = N("ShaderNodeMapRange", "Toon Factor", (-800, 220))
    toon.clamp = True
    link(x_clamped.outputs[0], toon.inputs["Value"])
    link(low.outputs[0], toon.inputs["From Min"])
    link(high.outputs[0], toon.inputs["From Max"])
    toon.inputs["To Min"].default_value = 0.0
    toon.inputs["To Max"].default_value = 1.0

    # ---------------- base / shade colours ----------------
    shade_tex = mix_rgb("MULTIPLY", "Shade x Texture", (-1300, 180))
    link(n_in.outputs["Shade Texture"], shade_tex.inputs[1])
    link(n_in.outputs["Shade Color"], shade_tex.inputs[2])

    tint_col = mix_rgb("MIX", "Shadow Tint", (-1300, 20))
    tint_col.inputs[1].default_value = (1.0, 1.0, 1.0, 1.0)
    link(n_in.outputs["Shade Tint Strength"], tint_col.inputs[0])
    link(n_in.outputs["Shadow Color"], tint_col.inputs[2])

    shade_final = mix_rgb("MULTIPLY", "Apply Shadow Tint", (-1100, 120))
    link(shade_tex.outputs["Color"], shade_final.inputs[1])
    link(tint_col.outputs["Color"], shade_final.inputs[2])

    toon_mix = mix_rgb("MIX", "Lit / Shade", (-850, 250))
    link(toon.outputs["Result"], toon_mix.inputs[0])
    link(shade_final.outputs["Color"], toon_mix.inputs[1])
    link(n_in.outputs["Base Color"], toon_mix.inputs[2])

    # ---------------- light colour tint ----------------
    light_tint = mix_rgb("MIX", "Light Colour", (-850, -80))
    light_tint.inputs[1].default_value = (1.0, 1.0, 1.0, 1.0)
    link(n_in.outputs["Light Tint"], light_tint.inputs[0])
    link(chroma.outputs[0], light_tint.inputs[2])

    lit_tinted = mix_rgb("MULTIPLY", "Tint Lit", (-600, 80))
    link(toon_mix.outputs["Color"], lit_tinted.inputs[1])
    link(light_tint.outputs["Color"], lit_tinted.inputs[2])

    # ---------------- exposure / brightness ----------------
    # Exposure follows the scene light level so the character blends into
    # bright or dark environments instead of glowing at full albedo.
    expo_base = math_node("MULTIPLY", "Light Gain", (-850, -300), x_clamped.outputs[0], 1.35)
    expo_add = math_node("ADD", "Light Exposure", (-700, -300), expo_base.outputs[0], n_in.outputs["Ambient Floor"])
    expo_clamp = math_node("MINIMUM", "Exposure Clamp", (-550, -300), expo_add.outputs[0], 1.25)
    expo_inv = math_node("SUBTRACT", "Exposure Delta", (-400, -340), expo_clamp.outputs[0], 1.0)
    expo_mix = math_node("MULTIPLY", "Light Response", (-250, -340), expo_inv.outputs[0], n_in.outputs["Light Response"])
    expo = math_node("ADD", "Final Exposure", (-100, -300), expo_mix.outputs[0], 1.0)
    value = math_node("MULTIPLY", "Brightness x Exposure", (200, -300), n_in.outputs["Brightness"], expo.outputs[0])

    hsv = N("ShaderNodeHueSaturation", "Saturation / Brightness", (350, 120))
    hsv.inputs["Hue"].default_value = 0.5
    link(lit_tinted.outputs["Color"], hsv.inputs["Color"])
    link(n_in.outputs["Saturation"], hsv.inputs["Saturation"])
    link(value.outputs[0], hsv.inputs["Value"])

    # ---------------- base-colour luma gate ----------------
    # Pure additive specular / rim on a black cloth would wash it grey, so both
    # effects are scaled by how bright the albedo is.
    base_bw = N("ShaderNodeRGBToBW", "Base Luma", (-1150, -700))
    link(n_in.outputs["Base Color"], base_bw.inputs[0])
    gate_mul = math_node("MULTIPLY", "Gate Gain", (-1000, -700), base_bw.outputs[0], 1.8)
    gate_clamp = math_node("MINIMUM", "Gate Clamp", (-850, -700), gate_mul.outputs[0], 1.0)
    gate = math_node("MAXIMUM", "Gate Floor", (-700, -700), gate_clamp.outputs[0], 0.06)

    # ---------------- specular (real glossy response) ----------------
    rough = math_node("SUBTRACT", "Glossy Roughness", (-1300, -480), 1.0, n_in.outputs["Specular Smoothness"])
    rough_clamped = math_node("MAXIMUM", "Roughness Floor", (-1150, -480), rough.outputs[0], 0.03)
    glossy = N("ShaderNodeBsdfGlossy", "Spec Probe", (-1000, -480))
    link(n_in.outputs["Normal"], glossy.inputs["Normal"])
    link(rough_clamped.outputs[0], glossy.inputs["Roughness"])
    spec_s2rgb = N("ShaderNodeShaderToRGB", "Spec to RGB", (-820, -480))
    link(glossy.outputs[0], spec_s2rgb.inputs[0])

    spec_dot = N("ShaderNodeVectorMath", "Spec Luma", (-640, -480))
    spec_dot.operation = "DOT_PRODUCT"
    link(spec_s2rgb.outputs["Color"], spec_dot.inputs[0])
    spec_dot.inputs[1].default_value = (0.2126, 0.7152, 0.0722)

    spec_mask = N("ShaderNodeMapRange", "Spec Mask", (-460, -480))
    spec_mask.clamp = True
    link(spec_dot.outputs["Value"], spec_mask.inputs["Value"])
    spec_mask.inputs["From Min"].default_value = 0.20
    spec_mask.inputs["From Max"].default_value = 0.75
    spec_mask.inputs["To Min"].default_value = 0.0
    spec_mask.inputs["To Max"].default_value = 1.0

    spec_tint_col = mix_rgb("MULTIPLY", "Spec Colour", (-460, -650))
    link(n_in.outputs["Specular Color"], spec_tint_col.inputs[1])
    link(light_tint.outputs["Color"], spec_tint_col.inputs[2])

    spec_col = mix_rgb("MIX", "Spec Masked", (-260, -480))
    spec_col.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)
    link(spec_mask.outputs["Result"], spec_col.inputs[0])
    link(spec_tint_col.outputs["Color"], spec_col.inputs[2])

    spec_scale = mix_rgb("MULTIPLY", "Spec Strength", (-80, -480))
    link(spec_col.outputs["Color"], spec_scale.inputs[1])
    spec_strength = math_node("MULTIPLY", "Spec Strength x Gate", (-260, -600), n_in.outputs["Specular Strength"], gate.outputs[0])
    link(spec_strength.outputs[0], spec_scale.inputs[2])

    # ---------------- rim light (fresnel, tinted by scene light) ----------------
    fresnel = N("ShaderNodeFresnel", "Rim Fresnel", (-1300, -850))
    fresnel.inputs["IOR"].default_value = 1.45
    link(geo.outputs["Normal"], fresnel.inputs["Normal"])

    rim_high = math_node("ADD", "Rim High", (-900, -950), n_in.outputs["Rim Threshold"], 0.06)
    rim_mask = N("ShaderNodeMapRange", "Rim Mask", (-700, -850))
    rim_mask.clamp = True
    link(fresnel.outputs["Fac"], rim_mask.inputs["Value"])
    link(n_in.outputs["Rim Threshold"], rim_mask.inputs["From Min"])
    link(rim_high.outputs[0], rim_mask.inputs["From Max"])
    rim_mask.inputs["To Min"].default_value = 0.0
    rim_mask.inputs["To Max"].default_value = 1.0

    rim_tint = mix_rgb("MULTIPLY", "Rim Colour", (-700, -1050))
    link(n_in.outputs["Rim Color"], rim_tint.inputs[1])
    link(light_tint.outputs["Color"], rim_tint.inputs[2])

    rim_col = mix_rgb("MIX", "Rim Masked", (-460, -850))
    rim_col.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)
    link(rim_mask.outputs["Result"], rim_col.inputs[0])
    link(rim_tint.outputs["Color"], rim_col.inputs[2])

    rim_scale = mix_rgb("MULTIPLY", "Rim Strength", (-260, -850))
    link(rim_col.outputs["Color"], rim_scale.inputs[1])
    rim_gated = N("ShaderNodeMath", "Rim Strength x Gate", (-460, -1000))
    rim_gated.operation = "MULTIPLY"
    link(n_in.outputs["Rim Strength"], rim_gated.inputs[0])
    link(gate.outputs[0], rim_gated.inputs[1])
    link(rim_gated.outputs[0], rim_scale.inputs[2])

    # ---------------- emission ----------------
    emit_scale = mix_rgb("MULTIPLY", "Emission Strength", (-460, -1200))
    link(n_in.outputs["Emission Color"], emit_scale.inputs[1])
    link(n_in.outputs["Emission Strength"], emit_scale.inputs[2])

    # ---------------- combine ----------------
    add_spec = mix_rgb("ADD", "Add Specular", (550, -100))
    link(hsv.outputs["Color"], add_spec.inputs[1])
    link(spec_scale.outputs["Color"], add_spec.inputs[2])

    add_rim = mix_rgb("ADD", "Add Rim", (700, -100))
    link(add_spec.outputs["Color"], add_rim.inputs[1])
    link(rim_scale.outputs["Color"], add_rim.inputs[2])

    add_emit = mix_rgb("ADD", "Add Emission", (850, -100))
    link(add_rim.outputs["Color"], add_emit.inputs[1])
    link(emit_scale.outputs["Color"], add_emit.inputs[2])

    final_emission = N("ShaderNodeEmission", "Final Emission", (1050, -100))
    final_emission.inputs["Strength"].default_value = 1.0
    link(add_emit.outputs["Color"], final_emission.inputs["Color"])

    transparent = N("ShaderNodeBsdfTransparent", "Transparent", (1050, -350))
    alpha_mix = N("ShaderNodeMixShader", "Alpha Mix", (1250, -150))
    link(n_in.outputs["Alpha"], alpha_mix.inputs[0])
    link(transparent.outputs[0], alpha_mix.inputs[1])
    link(final_emission.outputs[0], alpha_mix.inputs[2])
    link(alpha_mix.outputs[0], n_out.inputs["Surface"])

    return group


def apply_shader_preset(group, preset_name):
    """Apply a named preset to the shader node group interface defaults."""
    preset = PRESET_DEFAULTS.get(preset_name)
    if not preset or not group:
        return False
    for sock in group.interface.items_tree:
        if sock.item_type != "SOCKET" or sock.in_out != "INPUT":
            continue
        for prop, socket_name in SYNC_SOCKET_MAP.items():
            if socket_name == sock.name and prop in preset:
                try:
                    sock.default_value = preset[prop]
                except Exception:
                    pass
                break
    return True


def apply_preset_to_group_node(node, preset_name):
    """Set all synchronised sockets on one material's shader group node."""
    preset = PRESET_DEFAULTS.get(preset_name)
    if not preset or not node:
        return
    for prop, socket_name in SYNC_SOCKET_MAP.items():
        if prop not in preset:
            continue
        if socket_name in node.inputs:
            try:
                node.inputs[socket_name].default_value = preset[prop]
            except Exception:
                pass


# ============================================================
# MTOON DETECTION & PARAMETER EXTRACTION
# ============================================================


def is_mtoon_material(material):
    """Check if a material uses MToon shading (v0.0 or v1.0)."""
    if not material or not material.use_nodes:
        return False

    try:
        ext = getattr(material, "vrm_addon_extension", None)
        if ext is not None:
            mtoon1 = getattr(ext, "mtoon1", None)
            if mtoon1 and getattr(mtoon1, "enabled", False):
                return True
    except Exception:
        pass

    if material.node_tree:
        for node in material.node_tree.nodes:
            if node.type == "GROUP" and node.node_tree:
                name = node.node_tree.name.lower()
                if "mtoon" in name:
                    return True
    return False


def is_anime_shader_material(material):
    """Check if a material already uses our anime shader."""
    if not material or not material.use_nodes or not material.node_tree:
        return False
    for node in material.node_tree.nodes:
        if node.type == "GROUP" and node.node_tree:
            if node.node_tree.name == SHADER_GROUP_NAME:
                return True
    return False


def _safe_color(value, fallback=(1.0, 1.0, 1.0, 1.0)):
    try:
        if value is None:
            return fallback
        seq = list(value)
        if len(seq) == 3:
            seq.append(1.0)
        return tuple(float(x) for x in seq[:4])
    except Exception:
        return fallback


def _is_white(color, tol=0.004):
    try:
        return all(abs(float(c) - 1.0) <= tol for c in color[:3])
    except Exception:
        return False


def _is_black(color, tol=0.004):
    try:
        return all(abs(float(c)) <= tol for c in color[:3])
    except Exception:
        return False


def _find_role_texture(tree, role):
    """Find an MToon texture image node by its role, e.g. BaseColor."""
    if not tree:
        return None
    key = f"Mtoon1{role}Texture"
    candidates = []
    for node in tree.nodes:
        if node.type != "TEX_IMAGE":
            continue
        if key in node.name:
            candidates.append(node)
    for node in candidates:
        try:
            if node.image is not None and node.image.size[0] > 0:
                return node
        except Exception:
            return node
    return candidates[0] if candidates else None


def extract_mtoon_params(material):
    """Extract MToon 1.0 parameters plus texture nodes for the anime shader."""
    params = {
        "base_color": (1.0, 1.0, 1.0, 1.0),
        "base_color_tex": None,
        "shade_color": (1.0, 1.0, 1.0, 1.0),
        "shade_tex": None,
        "normal_tex": None,
        "normal_strength": 1.0,
        "emissive_color": (0.0, 0.0, 0.0, 1.0),
        "emissive_tex": None,
        "alpha_mode": "OPAQUE",
        "alpha_cutoff": 0.5,
        "double_sided": False,
        "toony": 0.9,
        "shift": 0.0,
        "outline_material": False,
    }
    if not material or not material.node_tree:
        return params

    tree = material.node_tree
    # texture nodes are reliably named by the VRM importer
    params["base_color_tex"] = _find_role_texture(tree, "BaseColor")
    params["shade_tex"] = _find_role_texture(tree, "ShadeMultiply")
    params["normal_tex"] = _find_role_texture(tree, "Normal")
    params["emissive_tex"] = _find_role_texture(tree, "Emissive")

    try:
        ext = getattr(material, "vrm_addon_extension", None)
        mtoon1 = getattr(ext, "mtoon1", None) if ext else None
        if mtoon1 and getattr(mtoon1, "enabled", False):
            pbr = getattr(mtoon1, "pbr_metallic_roughness", None)
            if pbr:
                params["base_color"] = _safe_color(getattr(pbr, "base_color_factor", None))
            params["alpha_mode"] = str(getattr(mtoon1, "alpha_mode", "OPAQUE") or "OPAQUE")
            params["alpha_cutoff"] = float(getattr(mtoon1, "alpha_cutoff", 0.5) or 0.5)
            params["double_sided"] = bool(getattr(mtoon1, "double_sided", False))

            nt = getattr(mtoon1, "normal_texture", None)
            if nt:
                params["normal_strength"] = float(getattr(nt, "scale", 1.0) or 1.0)

            emissive_factor = _safe_color(getattr(mtoon1, "emissive_factor", None), (0, 0, 0, 1))
            emissive_strength = 1.0
            try:
                khr = getattr(getattr(mtoon1, "extensions", None), "khr_materials_emissive_strength", None)
                if khr:
                    emissive_strength = float(getattr(khr, "emissive_strength", 1.0) or 1.0)
            except Exception:
                pass
            if emissive_strength == 0.0:
                emissive_strength = 1.0
            params["emissive_color"] = tuple(c * emissive_strength for c in emissive_factor)

            vm = getattr(getattr(mtoon1, "extensions", None), "vrmc_materials_mtoon", None)
            if vm:
                params["shade_color"] = _safe_color(getattr(vm, "shade_color_factor", None))
                try:
                    params["toony"] = float(getattr(vm, "shading_toony_factor", 0.9) or 0.9)
                except Exception:
                    pass
                try:
                    params["shift"] = float(getattr(vm, "shading_shift_factor", 0.0) or 0.0)
                except Exception:
                    pass
    except Exception:
        pass

    # Materials whose node group is an outline pass (not slot materials) would
    # carry "Is Outline" = 1; slot materials never do, so nothing to skip here.
    return params


def _extract_principled_params(material, params):
    """Fallback extraction for plain Principled BSDF materials."""
    try:
        tree = material.node_tree
        if not tree:
            return
        for node in tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            bc = node.inputs.get("Base Color")
            if bc:
                if bc.is_linked:
                    for link in bc.links:
                        if link.from_node.type == "TEX_IMAGE":
                            params["base_color_tex"] = link.from_node
                            break
                else:
                    params["base_color"] = tuple(bc.default_value)
            alpha = node.inputs.get("Alpha")
            if alpha:
                if alpha.is_linked:
                    for link in alpha.links:
                        if link.from_node.type == "TEX_IMAGE":
                            params["alpha_mode"] = "BLEND"
                            break
                elif alpha.default_value < 1.0:
                    params["alpha_mode"] = "BLEND"
            em = node.inputs.get("Emission Color")
            em_strength = node.inputs.get("Emission Strength")
            if em:
                if em.is_linked:
                    for link in em.links:
                        if link.from_node.type == "TEX_IMAGE":
                            params["emissive_tex"] = link.from_node
                            break
                else:
                    params["emissive_color"] = tuple(em.default_value)
                if em_strength:
                    params["emissive_color"] = tuple(
                        c * float(em_strength.default_value) for c in params["emissive_color"]
                    )
            nm = node.inputs.get("Normal")
            if nm and nm.is_linked:
                for link in nm.links:
                    if link.from_node.type == "NORMAL_MAP":
                        for nlink in link.from_node.inputs["Color"].links:
                            if nlink.from_node.type == "TEX_IMAGE":
                                params["normal_tex"] = nlink.from_node
                                break
                        params["normal_strength"] = link.from_node.inputs["Strength"].default_value
                        break
            break
    except Exception:
        pass


# ============================================================
# MATERIAL CONVERSION
# ============================================================


def _ensure_uv(tree, tex_node, texcoord_node):
    """Make sure a texture node has a usable UV vector input."""
    if not tex_node or not texcoord_node:
        return
    vec = tex_node.inputs.get("Vector")
    if not vec:
        return
    if vec.is_linked:
        src = vec.links[0].from_node
        if src.type == "MAPPING":
            mvec = src.inputs.get("Vector")
            if mvec and not mvec.is_linked:
                tree.links.new(texcoord_node.outputs["UV"], mvec)
        elif src.type in {"UVMAP", "TEX_COORD"}:
            return
        else:
            # link comes from a node that will be deleted -> replace
            tree.links.new(texcoord_node.outputs["UV"], vec)
    else:
        tree.links.new(texcoord_node.outputs["UV"], vec)


def convert_material_to_anime(material, context, preset_name="anime_clean"):
    """Convert a single material to the anime shader, preserving MToon data."""
    if not material:
        return False
    if is_anime_shader_material(material):
        return True
    if "MToon Outline" in material.name:
        return False
    if not material.use_nodes:
        material.use_nodes = True
    tree = material.node_tree
    if not tree:
        return False

    group = ensure_anime_shader_group(context)
    params = extract_mtoon_params(material)
    if not params.get("base_color_tex") and not is_mtoon_material(material):
        _extract_principled_params(material, params)

    # Textures that survive the cleanup; everything else is rebuilt.
    keep_types = {"TEX_IMAGE", "MAPPING"}
    keep_nodes = [n for n in tree.nodes if n.type in keep_types]
    for node in list(tree.nodes):
        if node not in keep_nodes:
            tree.nodes.remove(node)

    # Create the anime shader group node and output
    group_node = tree.nodes.new("ShaderNodeGroup")
    group_node.node_tree = group
    group_node.location = (0, 0)
    group_node.label = "VRM Anime Shader"
    mat_output = tree.nodes.new("ShaderNodeOutputMaterial")
    mat_output.location = (420, 0)
    tree.links.new(group_node.outputs["Surface"], mat_output.inputs["Surface"])

    texcoord = tree.nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-1100, -400)

    used_tex = set()

    # ---- base colour ----
    base_tex = params.get("base_color_tex")
    if base_tex:
        used_tex.add(base_tex)
        _ensure_uv(tree, base_tex, texcoord)
        base_tex.location = (-800, 300)
        base_out = base_tex.outputs["Color"]
        if not _is_white(params.get("base_color", (1, 1, 1, 1))):
            factor = tree.nodes.new("ShaderNodeMixRGB")
            factor.blend_type = "MULTIPLY"
            factor.location = (-550, 320)
            factor.inputs[0].default_value = 1.0
            factor.inputs[2].default_value = params["base_color"]
            tree.links.new(base_out, factor.inputs[1])
            base_out = factor.outputs["Color"]
        tree.links.new(base_out, group_node.inputs["Base Color"])
        base_alpha = base_tex.outputs["Alpha"]
        if params["base_color"][3] < 0.999:
            a_mul = tree.nodes.new("ShaderNodeMath")
            a_mul.operation = "MULTIPLY"
            a_mul.location = (-550, 0)
            a_mul.inputs[1].default_value = params["base_color"][3]
            tree.links.new(base_alpha, a_mul.inputs[0])
            base_alpha = a_mul.outputs[0]
    else:
        group_node.inputs["Base Color"].default_value = params.get("base_color", (1, 1, 1, 1))
        base_alpha = None

    # ---- shade colour / texture ----
    group_node.inputs["Shade Color"].default_value = params.get("shade_color", (1, 1, 1, 1))
    group_node.inputs["Shade Shift"].default_value = params.get("shift", 0.0)
    group_node.inputs["Shade Toony"].default_value = params.get("toony", 0.9)
    shade_tex = params.get("shade_tex")
    if shade_tex and shade_tex.image:
        used_tex.add(shade_tex)
        _ensure_uv(tree, shade_tex, texcoord)
        shade_tex.location = (-800, 100)
        tree.links.new(shade_tex.outputs["Color"], group_node.inputs["Shade Texture"])

    # ---- normal map ----
    normal_tex = params.get("normal_tex")
    normal_map = tree.nodes.new("ShaderNodeNormalMap")
    normal_map.location = (-550, -200)
    normal_map.inputs["Strength"].default_value = params.get("normal_strength", 1.0)
    if normal_tex and normal_tex.image:
        used_tex.add(normal_tex)
        _ensure_uv(tree, normal_tex, texcoord)
        normal_tex.location = (-800, -200)
        tree.links.new(normal_tex.outputs["Color"], normal_map.inputs["Color"])
    else:
        flat = tree.nodes.new("ShaderNodeRGB")
        flat.location = (-800, -260)
        flat.outputs[0].default_value = (0.5, 0.5, 1.0, 1.0)
        tree.links.new(flat.outputs[0], normal_map.inputs["Color"])
    tree.links.new(normal_map.outputs["Normal"], group_node.inputs["Normal"])

    # ---- emission ----
    emissive_tex = params.get("emissive_tex")
    emissive_color = params.get("emissive_color", (0, 0, 0, 1))
    if emissive_tex and emissive_tex.image:
        used_tex.add(emissive_tex)
        _ensure_uv(tree, emissive_tex, texcoord)
        emissive_tex.location = (-800, -500)
        if _is_white(emissive_color):
            tree.links.new(emissive_tex.outputs["Color"], group_node.inputs["Emission Color"])
        elif not _is_black(emissive_color):
            e_mul = tree.nodes.new("ShaderNodeMixRGB")
            e_mul.blend_type = "MULTIPLY"
            e_mul.location = (-550, -500)
            e_mul.inputs[0].default_value = 1.0
            e_mul.inputs[2].default_value = emissive_color
            tree.links.new(emissive_tex.outputs["Color"], e_mul.inputs[1])
            tree.links.new(e_mul.outputs["Color"], group_node.inputs["Emission Color"])
    else:
        group_node.inputs["Emission Color"].default_value = emissive_color

    # ---- alpha ----
    if base_alpha is not None:
        alpha_mode = params.get("alpha_mode", "OPAQUE")
        if alpha_mode == "MASK":
            cut = tree.nodes.new("ShaderNodeMath")
            cut.operation = "GREATER_THAN"
            cut.location = (-250, -50)
            cut.inputs[1].default_value = max(0.001, min(0.999, params.get("alpha_cutoff", 0.5)))
            tree.links.new(base_alpha, cut.inputs[0])
            tree.links.new(cut.outputs[0], group_node.inputs["Alpha"])
        elif alpha_mode == "BLEND":
            tree.links.new(base_alpha, group_node.inputs["Alpha"])

    # ---- preset defaults on this material's group node ----
    apply_preset_to_group_node(group_node, preset_name)

    # ---- material settings ----
    _set_blend_mode(material, params.get("alpha_mode", "OPAQUE"), params.get("alpha_cutoff", 0.5))
    try:
        material.use_backface_culling = not params.get("double_sided", False)
    except Exception:
        pass

    # remove unused texture nodes to keep the tree readable
    for node in list(tree.nodes):
        if node.type == "TEX_IMAGE" and node not in used_tex:
            tree.nodes.remove(node)
    for node in list(tree.nodes):
        if node.type == "MAPPING" and not node.outputs[0].is_linked:
            tree.nodes.remove(node)

    return True


def _set_blend_mode(material, alpha_mode, alpha_cutoff=0.5):
    """Set the material blend mode safely across Blender versions."""
    if bpy.app.version < (4, 2, 0):
        if alpha_mode == "BLEND":
            material.blend_method = "BLEND"
            material.shadow_method = "CLIP"
        elif alpha_mode == "MASK":
            material.blend_method = "CLIP"
            material.shadow_method = "CLIP"
            material.alpha_threshold = alpha_cutoff
        else:
            material.blend_method = "OPAQUE"
            material.shadow_method = "OPAQUE"
    else:
        if alpha_mode == "BLEND":
            material.surface_render_method = "BLENDED"
        elif alpha_mode == "MASK":
            material.surface_render_method = "DITHERED"
            try:
                material.alpha_threshold = alpha_cutoff
            except Exception:
                pass
        else:
            material.surface_render_method = "DITHERED"
    return True


def convert_armature_materials(armature_obj, context, preset_name="anime_clean"):
    """Convert all materials on meshes parented to the given armature."""
    if not armature_obj or armature_obj.type != "ARMATURE":
        return 0, 0

    converted = 0
    skipped = 0
    seen = set()
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if obj.parent != armature_obj:
            continue
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or mat.name in seen:
                continue
            seen.add(mat.name)
            if is_anime_shader_material(mat):
                skipped += 1
                continue
            if "MToon Outline" in mat.name:
                skipped += 1
                continue
            if convert_material_to_anime(mat, context, preset_name):
                converted += 1
            else:
                skipped += 1
    return converted, skipped


# ============================================================
# OPERATORS
# ============================================================


class VAS_OT_convert(Operator):
    """Convert all MToon materials on the selected armature to anime shader"""

    bl_idname = "vas.convert_mtoon"
    bl_label = "Convert MToon to Anime"
    bl_description = "Convert all MToon materials on selected armature to anime shader"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "ARMATURE"

    def execute(self, context):
        armature = context.active_object
        preset = context.scene.vas_props.preset
        converted, skipped = convert_armature_materials(armature, context, preset)
        if converted == 0 and skipped == 0:
            self.report({"WARNING"}, "No materials found on meshes parented to this armature")
        elif converted > 0:
            self.report({"INFO"}, f"Converted {converted} material(s), skipped {skipped}")
        else:
            self.report({"INFO"}, f"All {skipped} material(s) already converted")
        return {"FINISHED"}


class VAS_OT_apply_preset(Operator):
    """Apply a shader preset to all anime shader materials on selected armature"""

    bl_idname = "vas.apply_preset"
    bl_label = "Apply Preset"
    bl_description = "Apply the selected preset to all anime shader materials"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "ARMATURE"

    def execute(self, context):
        preset_name = context.scene.vas_props.preset
        preset = PRESET_DEFAULTS.get(preset_name)
        if not preset:
            self.report({"ERROR"}, f"Preset '{preset_name}' not found")
            return {"CANCELLED"}
        group = bpy.data.node_groups.get(SHADER_GROUP_NAME)
        if group:
            apply_shader_preset(group, preset_name)
        props = context.scene.vas_props
        for attr in SYNC_SOCKET_MAP:
            if attr in preset and hasattr(props, attr):
                try:
                    setattr(props, attr, preset[attr])
                except Exception:
                    pass
        self.report({"INFO"}, f"Applied preset '{preset['label']}' to all materials")
        return {"FINISHED"}


class VAS_OT_switch_preset(Operator):
    """Switch to a different preset"""

    bl_idname = "vas.switch_preset"
    bl_label = "Switch Preset"
    bl_description = "Switch to a different anime shader preset"
    bl_options = {"REGISTER", "UNDO"}

    preset_name: StringProperty(name="Preset Name")

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        preset = PRESET_DEFAULTS.get(self.preset_name)
        if not preset:
            self.report({"ERROR"}, f"Preset '{self.preset_name}' not found")
            return {"CANCELLED"}
        context.scene.vas_props.preset = self.preset_name
        group = bpy.data.node_groups.get(SHADER_GROUP_NAME)
        if group:
            apply_shader_preset(group, self.preset_name)
        props = context.scene.vas_props
        for attr in SYNC_SOCKET_MAP:
            if attr in preset and hasattr(props, attr):
                try:
                    setattr(props, attr, preset[attr])
                except Exception:
                    pass
        self.report({"INFO"}, f"Switched to preset: {preset['label']}")
        return {"FINISHED"}


class VAS_OT_reload(Operator):
    """Reload the VRM Anime Shader addon"""

    bl_idname = "vas.reload_addon"
    bl_label = "Reload Addon"
    bl_description = "Reload the VRM Anime Shader addon without restarting Blender"

    def execute(self, context):
        import importlib
        import sys

        module_name = __name__
        mod = sys.modules.get(module_name)
        if mod:
            try:
                unregister()
            except Exception:
                pass
            importlib.reload(mod)
            try:
                mod.register()
                self.report({"INFO"}, "VRM Anime Shader reloaded successfully")
            except Exception as e:
                self.report({"ERROR"}, f"Reload failed: {e}")
                return {"CANCELLED"}
        else:
            self.report({"WARNING"}, "Module not found in sys.modules")
        return {"FINISHED"}


class VAS_OT_rebuild_shader(Operator):
    """Rebuild the anime shader node group"""

    bl_idname = "vas.rebuild_shader"
    bl_label = "Rebuild Shader"
    bl_description = "Delete and rebuild the anime shader node group"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        existing = bpy.data.node_groups.get(SHADER_GROUP_NAME)
        if existing:
            bpy.data.node_groups.remove(existing)
        ensure_anime_shader_group(context)
        self.report({"INFO"}, "Anime shader node group rebuilt")
        return {"FINISHED"}


# ============================================================
# CUSTOM PROPERTIES
# ============================================================


def _sync_param_to_all(prop_name, value):
    """Push a shader parameter value to ALL anime shader materials."""
    socket_name = SYNC_SOCKET_MAP.get(prop_name, prop_name)
    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
        value = tuple(value)
    for mat in bpy.data.materials:
        if not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "GROUP" and node.node_tree and node.node_tree.name == SHADER_GROUP_NAME:
                if socket_name in node.inputs:
                    try:
                        node.inputs[socket_name].default_value = value
                    except Exception:
                        pass
                break


def _make_update(param_name):
    def update_fn(self, context):
        _sync_param_to_all(param_name, getattr(self, param_name))

    return update_fn


def _preset_default(prop, fallback):
    return PRESET_DEFAULTS["anime_clean"].get(prop, fallback)


class VAS_Properties(PropertyGroup):
    preset: EnumProperty(
        name="Shader Preset",
        description="Select an anime shader preset",
        items=[(k, v["label"], f"Apply {v['label']} style preset") for k, v in PRESET_DEFAULTS.items()],
        default="anime_clean",
    )

    shadow_color: bpy.props.FloatVectorProperty(
        name="Shadow Color", subtype="COLOR", size=4,
        default=_preset_default("shadow_color", (0.84, 0.8, 0.95, 1.0)),
        update=_make_update("shadow_color"),
    )
    shadow_threshold: bpy.props.FloatProperty(
        name="Threshold", default=_preset_default("shadow_threshold", 0.5), min=0.0, max=1.0,
        subtype="FACTOR", update=_make_update("shadow_threshold"),
    )
    shadow_smoothness: bpy.props.FloatProperty(
        name="Smoothness", default=_preset_default("shadow_smoothness", 0.05), min=0.0, max=0.5,
        update=_make_update("shadow_smoothness"),
    )
    shade_tint_strength: bpy.props.FloatProperty(
        name="Tint Strength", default=_preset_default("shade_tint_strength", 0.2), min=0.0, max=1.0,
        subtype="FACTOR", update=_make_update("shade_tint_strength"),
    )
    shift_influence: bpy.props.FloatProperty(
        name="MToon Shift", default=_preset_default("shift_influence", 0.42), min=0.0, max=1.5,
        subtype="FACTOR", update=_make_update("shift_influence"),
    )
    light_normalize: bpy.props.FloatProperty(
        name="Light Normalize", default=_preset_default("light_normalize", 3.0), min=0.1, max=20.0,
        update=_make_update("light_normalize"),
    )
    ambient_floor: bpy.props.FloatProperty(
        name="Ambient Floor", default=_preset_default("ambient_floor", 0.3), min=0.0, max=1.0,
        subtype="FACTOR", update=_make_update("ambient_floor"),
    )
    light_response: bpy.props.FloatProperty(
        name="Light Response", default=_preset_default("light_response", 0.6), min=0.0, max=1.0,
        subtype="FACTOR", update=_make_update("light_response"),
    )
    light_tint: bpy.props.FloatProperty(
        name="Light Tint", default=_preset_default("light_tint", 0.3), min=0.0, max=1.0,
        subtype="FACTOR", update=_make_update("light_tint"),
    )
    rim_color: bpy.props.FloatVectorProperty(
        name="Rim Color", subtype="COLOR", size=4,
        default=_preset_default("rim_color", (0.85, 0.88, 1.0, 1.0)),
        update=_make_update("rim_color"),
    )
    rim_strength: bpy.props.FloatProperty(
        name="Strength", default=_preset_default("rim_strength", 0.12), min=0.0, max=2.0,
        update=_make_update("rim_strength"),
    )
    rim_threshold: bpy.props.FloatProperty(
        name="Threshold", default=_preset_default("rim_threshold", 0.62), min=0.0, max=1.0,
        subtype="FACTOR", update=_make_update("rim_threshold"),
    )
    specular_color: bpy.props.FloatVectorProperty(
        name="Specular Color", subtype="COLOR", size=4,
        default=_preset_default("specular_color", (1, 1, 1, 1)),
        update=_make_update("specular_color"),
    )
    specular_strength: bpy.props.FloatProperty(
        name="Strength", default=_preset_default("specular_strength", 0.12), min=0.0, max=2.0,
        update=_make_update("specular_strength"),
    )
    specular_smoothness: bpy.props.FloatProperty(
        name="Smoothness", default=_preset_default("specular_smoothness", 0.35), min=0.0, max=1.0,
        update=_make_update("specular_smoothness"),
    )
    saturation: bpy.props.FloatProperty(
        name="Saturation", default=_preset_default("saturation", 1.02), min=0.0, max=2.0,
        update=_make_update("saturation"),
    )
    brightness: bpy.props.FloatProperty(
        name="Brightness", default=_preset_default("brightness", 1.0), min=0.0, max=2.0,
        update=_make_update("brightness"),
    )
    emission_strength: bpy.props.FloatProperty(
        name="Emission", default=_preset_default("emission_strength", 1.0), min=0.0, max=10.0,
        update=_make_update("emission_strength"),
    )


# ============================================================
# UI PANEL
# ============================================================


class VAS_PT_main(Panel):
    """Main panel for VRM Anime Shader"""

    bl_label = "VRM Anime Shader"
    bl_idname = "VAS_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Anime Shader"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        row = layout.row(align=True)
        row.operator("vas.reload_addon", text="Reload", icon="FILE_REFRESH")
        row.operator("vas.rebuild_shader", text="Rebuild Shader", icon="MODIFIER")

        box = layout.box()
        box.label(text="Material Conversion", icon="MATERIAL")
        row = box.row(align=True)
        row.enabled = bool(obj and obj.type == "ARMATURE")
        row.operator("vas.convert_mtoon", icon="PLAY")

        if obj and obj.type == "ARMATURE":
            mesh_count = sum(1 for o in bpy.data.objects if o.type == "MESH" and o.parent == obj)
            anime_count = 0
            mtoon_count = 0
            for o in bpy.data.objects:
                if o.type != "MESH" or o.parent != obj:
                    continue
                for slot in o.material_slots:
                    mat = slot.material
                    if not mat:
                        continue
                    if is_anime_shader_material(mat):
                        anime_count += 1
                    elif is_mtoon_material(mat):
                        mtoon_count += 1
            box.label(text=f"Meshes: {mesh_count} | Anime: {anime_count} | MToon: {mtoon_count}", icon="INFO")
        elif obj:
            box.label(text=f"Selected: {obj.name} (not armature)", icon="ERROR")
        else:
            box.label(text="Select an armature", icon="INFO")

        box = layout.box()
        box.label(text="Shader Presets", icon="PRESET")
        box.prop(context.scene.vas_props, "preset", text="")
        row = box.row(align=True)
        row.operator("vas.apply_preset", icon="CHECKMARK")
        col = box.column(align=True)
        for key, preset in PRESET_DEFAULTS.items():
            row = col.row(align=True)
            op = row.operator(
                "vas.switch_preset",
                text=preset["label"],
                icon="SHADING_SOLID" if key == context.scene.vas_props.preset else "NONE",
            )
            op.preset_name = key

        box = layout.box()
        box.label(text="Shader Parameters", icon="PREFERENCES")
        group = bpy.data.node_groups.get(SHADER_GROUP_NAME)
        if not group:
            box.label(text="No shader group found", icon="ERROR")
            return

        active_mat = None
        if obj and obj.type == "MESH":
            if obj.data.materials:
                active_mat = obj.data.materials[0]
        elif obj and obj.type == "ARMATURE":
            for o in bpy.data.objects:
                if o.type == "MESH" and o.parent == obj:
                    for slot in o.material_slots:
                        if slot.material and is_anime_shader_material(slot.material):
                            active_mat = slot.material
                            break
                    if active_mat:
                        break

        if not active_mat:
            box.label(text="No anime material found", icon="INFO")
            return

        # Panel is read-only: never write to scene/material data here (Blender
        # forbids ID writes from a panel draw callback). Shader parameters are
        # pushed to materials by the preset operators and scene property updates.
        self._draw_shader_params(box, context)

    def _draw_shader_params(self, box, context):
        props = context.scene.vas_props
        col = box.column(align=True)

        def safe_prop(target, attr, label):
            if not hasattr(props, attr):
                target.row().label(text=f"{label}: (rebuild shader)", icon="ERROR")
                return
            target.prop(props, attr, text=label)

        sub = col.box()
        sub.label(text="Shading", icon="SHADING_RENDERED")
        safe_prop(sub, "shadow_threshold", "Threshold")
        safe_prop(sub, "shadow_smoothness", "Smoothness")
        safe_prop(sub, "shift_influence", "MToon Shift")
        safe_prop(sub, "shade_tint_strength", "Tint Strength")
        safe_prop(sub, "shadow_color", "Tint Color")
        safe_prop(sub, "saturation", "Saturation")
        safe_prop(sub, "brightness", "Brightness")

        sub = col.box()
        sub.label(text="Scene Light", icon="LIGHT_SUN")
        safe_prop(sub, "light_normalize", "Light Normalize")
        safe_prop(sub, "ambient_floor", "Ambient Floor")
        safe_prop(sub, "light_response", "Light Response")
        safe_prop(sub, "light_tint", "Light Color Tint")

        sub = col.box()
        sub.label(text="Rim Light", icon="LIGHT_SUN")
        safe_prop(sub, "rim_color", "Color")
        safe_prop(sub, "rim_strength", "Strength")
        safe_prop(sub, "rim_threshold", "Threshold")

        sub = col.box()
        sub.label(text="Specular", icon="LIGHT")
        safe_prop(sub, "specular_color", "Color")
        safe_prop(sub, "specular_strength", "Strength")
        safe_prop(sub, "specular_smoothness", "Smoothness")

        sub = col.box()
        sub.label(text="Emission", icon="LIGHT_DATA")
        safe_prop(sub, "emission_strength", "Emission")


class VAS_PT_material_list(Panel):
    """Sub-panel showing materials on the armature"""

    bl_label = "Material List"
    bl_idname = "VAS_PT_material_list"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Anime Shader"
    bl_parent_id = "VAS_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        for mesh_obj in bpy.data.objects:
            if mesh_obj.type != "MESH" or mesh_obj.parent != obj:
                continue
            box = layout.box()
            box.label(text=mesh_obj.name, icon="OBJECT_DATA")
            for slot in mesh_obj.material_slots:
                mat = slot.material
                if not mat:
                    continue
                row = box.row(align=True)
                if is_anime_shader_material(mat):
                    row.label(text=f"  {mat.name}", icon="CHECKMARK")
                elif is_mtoon_material(mat):
                    row.label(text=f"  {mat.name}", icon="MATERIAL")
                else:
                    row.label(text=f"  {mat.name}", icon="QUESTION")


# ============================================================
# REGISTRATION
# ============================================================

classes = (
    VAS_Properties,
    VAS_OT_convert,
    VAS_OT_apply_preset,
    VAS_OT_switch_preset,
    VAS_OT_reload,
    VAS_OT_rebuild_shader,
    VAS_PT_main,
    VAS_PT_material_list,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vas_props = PointerProperty(type=VAS_Properties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.vas_props


if __name__ == "__main__":
    register()

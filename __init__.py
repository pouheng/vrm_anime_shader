bl_info = {
    "name": "VRM Anime Shader - MToon to Anime Converter",
    "author": "opencode",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Anime Shader",
    "description": "Convert VRM MToon materials to anime-style EEVEE shaders with preset switching",
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

PRESET_DEFAULTS = {
    "anime_clean": {
        "label": "Anime Clean",
        "shadow_color": (0.35, 0.25, 0.40, 1.0),
        "shadow_threshold": 0.42,
        "shadow_smoothness": 0.03,
        "rim_color": (0.85, 0.85, 0.95, 1.0),
        "rim_strength": 0.6,
        "rim_threshold": 0.65,
        "specular_color": (1.0, 1.0, 1.0, 1.0),
        "specular_strength": 0.35,
        "specular_smoothness": 0.18,
        "shadow_tint_strength": 0.5,
        "saturation": 1.1,
        "brightness": 1.0,
        "emission_strength": 0.0,
    },
    "wuthering_waves": {
        "label": "Wuthering Waves",
        "shadow_color": (0.30, 0.22, 0.45, 1.0),
        "shadow_threshold": 0.38,
        "shadow_smoothness": 0.06,
        "rim_color": (0.70, 0.75, 1.0, 1.0),
        "rim_strength": 0.75,
        "rim_threshold": 0.55,
        "specular_color": (0.95, 0.95, 1.0, 1.0),
        "specular_strength": 0.45,
        "specular_smoothness": 0.22,
        "shadow_tint_strength": 0.6,
        "saturation": 1.25,
        "brightness": 1.05,
        "emission_strength": 0.0,
    },
    "genshin_impact": {
        "label": "Genshin Impact",
        "shadow_color": (0.40, 0.30, 0.45, 1.0),
        "shadow_threshold": 0.44,
        "shadow_smoothness": 0.02,
        "rim_color": (0.90, 0.88, 1.0, 1.0),
        "rim_strength": 0.5,
        "rim_threshold": 0.70,
        "specular_color": (1.0, 0.98, 0.95, 1.0),
        "specular_strength": 0.30,
        "specular_smoothness": 0.15,
        "shadow_tint_strength": 0.45,
        "saturation": 1.15,
        "brightness": 1.0,
        "emission_strength": 0.0,
    },
    "honkai_star": {
        "label": "Honkai Star Rail",
        "shadow_color": (0.28, 0.20, 0.42, 1.0),
        "shadow_threshold": 0.40,
        "shadow_smoothness": 0.04,
        "rim_color": (0.75, 0.80, 1.0, 1.0),
        "rim_strength": 0.70,
        "rim_threshold": 0.60,
        "specular_color": (0.90, 0.92, 1.0, 1.0),
        "specular_strength": 0.40,
        "specular_smoothness": 0.20,
        "shadow_tint_strength": 0.55,
        "saturation": 1.20,
        "brightness": 1.02,
        "emission_strength": 0.0,
    },
    "flat_shade": {
        "label": "Flat Cel Shade",
        "shadow_color": (0.25, 0.20, 0.30, 1.0),
        "shadow_threshold": 0.50,
        "shadow_smoothness": 0.0,
        "rim_color": (1.0, 1.0, 1.0, 1.0),
        "rim_strength": 0.0,
        "rim_threshold": 0.80,
        "specular_color": (1.0, 1.0, 1.0, 1.0),
        "specular_strength": 0.0,
        "specular_smoothness": 0.10,
        "shadow_tint_strength": 0.3,
        "saturation": 1.0,
        "brightness": 1.0,
        "emission_strength": 0.0,
    },
    "soft_anime": {
        "label": "Soft Anime",
        "shadow_color": (0.42, 0.35, 0.48, 1.0),
        "shadow_threshold": 0.40,
        "shadow_smoothness": 0.10,
        "rim_color": (0.80, 0.82, 0.95, 1.0),
        "rim_strength": 0.45,
        "rim_threshold": 0.60,
        "specular_color": (1.0, 0.98, 0.95, 1.0),
        "specular_strength": 0.25,
        "specular_smoothness": 0.25,
        "shadow_tint_strength": 0.4,
        "saturation": 1.05,
        "brightness": 1.03,
        "emission_strength": 0.0,
    },
}


# ============================================================
# SHADER BUILDER
# ============================================================


def _new_socket(group, name, in_out, socket_type, **kwargs):
    """Create a socket on a ShaderNodeGroup interface (Blender 4.0+)."""
    sock = group.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
    for k, v in kwargs.items():
        setattr(sock, k, v)
    return sock


def ensure_anime_shader_group(context):
    """Create or get the anime shader node group. Rebuilds if interface is stale."""
    existing = bpy.data.node_groups.get(SHADER_GROUP_NAME)
    if existing and existing.type == "SHADER":
        # Build socket name set, separate by direction
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
        required_inputs = {
            "Base Color",
            "Shadow Color",
            "Shadow Threshold",
            "Shadow Smoothness",
            "Rim Color",
            "Rim Strength",
            "Rim Threshold",
            "Specular Color",
            "Specular Strength",
            "Specular Smoothness",
            "Shadow Tint Strength",
            "Saturation",
            "Brightness",
            "Emission Strength",
            "Emission Color",
            "Alpha",
        }
        required_outputs = {"Surface"}
        if required_inputs.issubset(existing_inputs) and required_outputs.issubset(
            existing_outputs
        ):
            return existing
        # Stale or incomplete group - remove and rebuild
        bpy.data.node_groups.remove(existing)
    elif existing:
        bpy.data.node_groups.remove(existing)
    return _build_anime_shader_group(context)


def _build_anime_shader_group(context):
    """Build the complete anime shader node group from scratch."""
    group = bpy.data.node_groups.new(SHADER_GROUP_NAME, "ShaderNodeTree")

    # --- Interface ---
    _new_socket(
        group,
        "Base Color",
        "INPUT",
        "NodeSocketColor",
        default_value=(1.0, 1.0, 1.0, 1.0),
    )
    _new_socket(
        group,
        "Shadow Color",
        "INPUT",
        "NodeSocketColor",
        default_value=(0.35, 0.25, 0.40, 1.0),
    )
    _new_socket(
        group,
        "Shadow Threshold",
        "INPUT",
        "NodeSocketFloat",
        default_value=0.42,
        min_value=0.0,
        max_value=1.0,
        subtype="FACTOR",
    )
    _new_socket(
        group,
        "Shadow Smoothness",
        "INPUT",
        "NodeSocketFloat",
        default_value=0.03,
        min_value=0.0,
        max_value=0.5,
    )
    _new_socket(
        group,
        "Rim Color",
        "INPUT",
        "NodeSocketColor",
        default_value=(0.85, 0.85, 0.95, 1.0),
    )
    _new_socket(
        group,
        "Rim Strength",
        "INPUT",
        "NodeSocketFloat",
        default_value=0.6,
        min_value=0.0,
        max_value=2.0,
    )
    _new_socket(
        group,
        "Rim Threshold",
        "INPUT",
        "NodeSocketFloat",
        default_value=0.65,
        min_value=0.0,
        max_value=1.0,
        subtype="FACTOR",
    )
    _new_socket(
        group,
        "Specular Color",
        "INPUT",
        "NodeSocketColor",
        default_value=(1.0, 1.0, 1.0, 1.0),
    )
    _new_socket(
        group,
        "Specular Strength",
        "INPUT",
        "NodeSocketFloat",
        default_value=0.35,
        min_value=0.0,
        max_value=2.0,
    )
    _new_socket(
        group,
        "Specular Smoothness",
        "INPUT",
        "NodeSocketFloat",
        default_value=0.18,
        min_value=0.01,
        max_value=1.0,
    )
    _new_socket(
        group,
        "Shadow Tint Strength",
        "INPUT",
        "NodeSocketFloat",
        default_value=0.5,
        min_value=0.0,
        max_value=1.0,
        subtype="FACTOR",
    )
    _new_socket(
        group,
        "Saturation",
        "INPUT",
        "NodeSocketFloat",
        default_value=1.1,
        min_value=0.0,
        max_value=3.0,
    )
    _new_socket(
        group,
        "Brightness",
        "INPUT",
        "NodeSocketFloat",
        default_value=1.0,
        min_value=0.0,
        max_value=3.0,
    )
    _new_socket(
        group,
        "Emission Strength",
        "INPUT",
        "NodeSocketFloat",
        default_value=0.0,
        min_value=0.0,
        max_value=10.0,
    )
    _new_socket(
        group,
        "Emission Color",
        "INPUT",
        "NodeSocketColor",
        default_value=(1.0, 1.0, 1.0, 1.0),
    )
    _new_socket(
        group,
        "Alpha",
        "INPUT",
        "NodeSocketFloat",
        default_value=1.0,
        min_value=0.0,
        max_value=1.0,
        subtype="FACTOR",
    )
    _new_socket(group, "Surface", "OUTPUT", "NodeSocketShader")

    nodes = group.nodes
    links = group.links

    # --- INPUT / OUTPUT nodes ---
    n_in = nodes.new("NodeGroupInput")
    n_in.location = (-1600, 0)

    n_out = nodes.new("NodeGroupOutput")
    n_out.location = (1200, 0)

    # --- Diffuse BSDF (Shader → ShaderToRGB → Color) ---
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.location = (-1200, 400)
    diffuse.label = "Diffuse BSDF"

    s2rgb_diff = nodes.new("ShaderNodeShaderToRGB")
    s2rgb_diff.location = (-1000, 400)
    s2rgb_diff.label = "Diffuse to RGB"

    # Minimum ambient so texture is visible even without scene lights
    ambient_min = nodes.new("ShaderNodeMath")
    ambient_min.operation = "ADD"
    ambient_min.location = (-900, 300)
    ambient_min.label = "Ambient Minimum"
    ambient_min.inputs[1].default_value = 0.25

    # --- Shadow: ColorRamp + Mix (all in Color domain) ---
    shadow_ramp = nodes.new("ShaderNodeValToRGB")
    shadow_ramp.location = (-700, 400)
    shadow_ramp.label = "Shadow Ramp"
    cr_elem = shadow_ramp.color_ramp
    cr_elem.interpolation = "LINEAR"
    cr_elem.elements[0].position = 0.0
    cr_elem.elements[0].color = (1, 1, 1, 1)
    cr_elem.elements[1].position = 0.5
    cr_elem.elements[1].color = (0, 0, 0, 1)

    shadow_mix = nodes.new("ShaderNodeMixRGB")
    shadow_mix.blend_type = "MULTIPLY"
    shadow_mix.location = (-600, 200)
    shadow_mix.label = "Shadow Tint"
    shadow_mix.inputs[0].default_value = 1.0

    tex_shadow_mix = nodes.new("ShaderNodeMixRGB")
    tex_shadow_mix.blend_type = "MIX"
    tex_shadow_mix.location = (-400, 400)
    tex_shadow_mix.label = "Apply Shadow"

    # --- HSV for saturation/brightness ---
    hsv = nodes.new("ShaderNodeHueSaturation")
    hsv.location = (-200, 500)
    hsv.label = "Sat/Bright"
    hsv.inputs["Hue"].default_value = 0.5

    # --- Emission overlay (MixRGB ADD in Color domain) ---
    emit_mix = nodes.new("ShaderNodeMixRGB")
    emit_mix.blend_type = "ADD"
    emit_mix.location = (0, 400)
    emit_mix.label = "Emission Overlay"

    # --- Fresnel → Rim Ramp (no ShaderToRGB needed) ---
    fresnel = nodes.new("ShaderNodeFresnel")
    fresnel.location = (-1200, -200)
    fresnel.label = "Fresnel"
    fresnel.inputs["IOR"].default_value = 1.45

    rim_ramp = nodes.new("ShaderNodeValToRGB")
    rim_ramp.location = (-1000, -200)
    rim_ramp.label = "Rim Ramp"
    rcr = rim_ramp.color_ramp
    rcr.interpolation = "CONSTANT"
    rcr.elements[0].position = 0.55
    rcr.elements[0].color = (0, 0, 0, 1)
    rcr.elements[1].position = 0.60
    rcr.elements[1].color = (1, 1, 1, 1)

    rim_mix = nodes.new("ShaderNodeMixRGB")
    rim_mix.blend_type = "MIX"
    rim_mix.location = (-800, -400)
    rim_mix.label = "Rim Tint"
    rim_mix.inputs[1].default_value = (0, 0, 0, 1)

    rim_add = nodes.new("ShaderNodeMixRGB")
    rim_add.blend_type = "ADD"
    rim_add.location = (-200, 100)
    rim_add.label = "Add Rim"

    # --- Specular: Diffuse + Glossy → ShaderToRGB → Color ops ---
    specular_mix = nodes.new("ShaderNodeMixShader")
    specular_mix.location = (-1000, -600)
    specular_mix.label = "Specular Mix"
    specular_mix.inputs[0].default_value = 0.15

    glossy = nodes.new("ShaderNodeBsdfGlossy")
    glossy.location = (-1200, -700)
    glossy.label = "Glossy"
    glossy.inputs["Roughness"].default_value = 0.18

    s2rgb_spec = nodes.new("ShaderNodeShaderToRGB")
    s2rgb_spec.location = (-800, -600)
    s2rgb_spec.label = "Spec to RGB"

    spec_ramp = nodes.new("ShaderNodeValToRGB")
    spec_ramp.location = (-600, -600)
    spec_ramp.label = "Spec Ramp"
    scr = spec_ramp.color_ramp
    scr.interpolation = "LINEAR"
    scr.elements[0].position = 0.0
    scr.elements[0].color = (0, 0, 0, 1)
    scr.elements[1].position = 0.35
    scr.elements[1].color = (1, 1, 1, 1)

    spec_tint = nodes.new("ShaderNodeMixRGB")
    spec_tint.blend_type = "MIX"
    spec_tint.location = (-400, -600)
    spec_tint.label = "Spec Tint"
    spec_tint.inputs[1].default_value = (0, 0, 0, 1)

    spec_overlay = nodes.new("ShaderNodeMixRGB")
    spec_overlay.blend_type = "ADD"
    spec_overlay.location = (200, 0)
    spec_overlay.label = "Add Specular"

    # --- Final Emission: convert Color → Shader for valid output ---
    final_emission = nodes.new("ShaderNodeEmission")
    final_emission.location = (600, 400)
    final_emission.label = "Final Emission"
    final_emission.inputs["Strength"].default_value = 1.0

    # --- Alpha: Transparent BSDF mix for MASK/BLEND materials ---
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (600, 100)
    transparent.label = "Transparent"

    alpha_mix = nodes.new("ShaderNodeMixShader")
    alpha_mix.location = (800, 300)
    alpha_mix.label = "Alpha Mix"

    # ============ LINKS ============

    # Main diffuse → shadow path (Shader → Color → Color ops)
    links.new(n_in.outputs["Base Color"], diffuse.inputs["Color"])
    links.new(diffuse.outputs[0], s2rgb_diff.inputs[0])
    links.new(s2rgb_diff.outputs["Color"], ambient_min.inputs[0])
    links.new(ambient_min.outputs[0], shadow_ramp.inputs["Fac"])
    links.new(n_in.outputs["Base Color"], shadow_mix.inputs[1])
    links.new(n_in.outputs["Shadow Color"], shadow_mix.inputs[2])
    links.new(shadow_ramp.outputs["Color"], shadow_mix.inputs[0])
    links.new(n_in.outputs["Base Color"], tex_shadow_mix.inputs[1])
    links.new(shadow_mix.outputs["Color"], tex_shadow_mix.inputs[2])
    links.new(shadow_ramp.outputs["Color"], tex_shadow_mix.inputs[0])
    links.new(tex_shadow_mix.outputs["Color"], hsv.inputs["Color"])
    links.new(n_in.outputs["Saturation"], hsv.inputs["Saturation"])
    links.new(n_in.outputs["Brightness"], hsv.inputs["Value"])

    # Emission overlay (Color domain, ADD)
    links.new(hsv.outputs["Color"], emit_mix.inputs[1])
    links.new(n_in.outputs["Emission Color"], emit_mix.inputs[2])
    links.new(n_in.outputs["Emission Strength"], emit_mix.inputs[0])

    # Rim (Fresnel Fac → Rim Ramp directly, no ShaderToRGB)
    links.new(fresnel.outputs["Fac"], rim_ramp.inputs["Fac"])
    links.new(rim_ramp.outputs["Color"], rim_mix.inputs[0])
    links.new(n_in.outputs["Rim Color"], rim_mix.inputs[2])
    links.new(emit_mix.outputs["Color"], rim_add.inputs[1])
    links.new(rim_mix.outputs["Color"], rim_add.inputs[2])
    links.new(n_in.outputs["Rim Strength"], rim_add.inputs[0])

    # Specular (Diffuse + Glossy → ShaderToRGB → Color ops)
    links.new(diffuse.outputs[0], specular_mix.inputs[1])
    links.new(glossy.outputs[0], specular_mix.inputs[2])
    links.new(specular_mix.outputs[0], s2rgb_spec.inputs[0])
    links.new(s2rgb_spec.outputs["Color"], spec_ramp.inputs["Fac"])
    links.new(spec_ramp.outputs["Color"], spec_tint.inputs[0])
    links.new(n_in.outputs["Specular Color"], spec_tint.inputs[2])
    links.new(n_in.outputs["Specular Smoothness"], glossy.inputs["Roughness"])
    links.new(n_in.outputs["Specular Strength"], spec_overlay.inputs[0])
    links.new(rim_add.outputs["Color"], spec_overlay.inputs[1])
    links.new(spec_tint.outputs["Color"], spec_overlay.inputs[2])

    # Final: Color → Shader via Emission, then alpha mix, then output
    links.new(spec_overlay.outputs["Color"], final_emission.inputs["Color"])
    links.new(final_emission.outputs[0], alpha_mix.inputs[2])
    links.new(transparent.outputs[0], alpha_mix.inputs[1])
    links.new(n_in.outputs["Alpha"], alpha_mix.inputs[0])
    links.new(alpha_mix.outputs[0], n_out.inputs["Surface"])

    return group


def apply_shader_preset(group, preset_name):
    """Apply a named preset to the shader node group defaults."""
    preset = PRESET_DEFAULTS.get(preset_name)
    if not preset:
        return False

    # Update group interface defaults
    for sock in group.interface.items_tree:
        if sock.item_type != "SOCKET":
            continue
        key = sock.name
        if key == "Shadow Color" and "shadow_color" in preset:
            sock.default_value = preset["shadow_color"]
        elif key == "Shadow Threshold" and "shadow_threshold" in preset:
            sock.default_value = preset["shadow_threshold"]
        elif key == "Shadow Smoothness" and "shadow_smoothness" in preset:
            sock.default_value = preset["shadow_smoothness"]
        elif key == "Rim Color" and "rim_color" in preset:
            sock.default_value = preset["rim_color"]
        elif key == "Rim Strength" and "rim_strength" in preset:
            sock.default_value = preset["rim_strength"]
        elif key == "Rim Threshold" and "rim_threshold" in preset:
            sock.default_value = preset["rim_threshold"]
        elif key == "Specular Color" and "specular_color" in preset:
            sock.default_value = preset["specular_color"]
        elif key == "Specular Strength" and "specular_strength" in preset:
            sock.default_value = preset["specular_strength"]
        elif key == "Specular Smoothness" and "specular_smoothness" in preset:
            sock.default_value = preset["specular_smoothness"]
        elif key == "Shadow Tint Strength" and "shadow_tint_strength" in preset:
            sock.default_value = preset["shadow_tint_strength"]
        elif key == "Saturation" and "saturation" in preset:
            sock.default_value = preset["saturation"]
        elif key == "Brightness" and "brightness" in preset:
            sock.default_value = preset["brightness"]
        elif key == "Emission Strength" and "emission_strength" in preset:
            sock.default_value = preset["emission_strength"]

    # Also update internal node defaults
    for node in group.nodes:
        if node.label == "Shadow Ramp":
            t = preset.get("shadow_threshold", 0.42)
            s = preset.get("shadow_smoothness", 0.03)
            node.color_ramp.elements[0].position = t
            node.color_ramp.elements[1].position = min(t + max(s, 0.001), 1.0)
        elif node.label == "Rim Ramp":
            rt = preset.get("rim_threshold", 0.65)
            node.color_ramp.elements[0].position = rt
            node.color_ramp.elements[1].position = min(rt + 0.05, 1.0)
        elif node.label == "Spec Ramp":
            sp = preset.get("specular_smoothness", 0.18)
            node.color_ramp.elements[0].position = 0.0
            node.color_ramp.elements[1].position = sp
        elif node.label == "Sat/Bright":
            node.inputs["Saturation"].default_value = preset.get("saturation", 1.1)
            node.inputs["Value"].default_value = preset.get("brightness", 1.0)
        elif node.label == "Glossy":
            node.inputs["Roughness"].default_value = preset.get(
                "specular_smoothness", 0.18
            )

    return True


# ============================================================
# MTOON DETECTION & PARAMETER EXTRACTION
# ============================================================


def is_mtoon_material(material):
    """Check if a material uses MToon shading (v0.0 or v1.0)."""
    if not material or not material.use_nodes:
        return False

    # Check VRM addon extension (MToon 1.0)
    try:
        ext = getattr(material, "vrm_addon_extension", None)
        if ext is not None:
            mtoon1 = getattr(ext, "mtoon1", None)
            if mtoon1 and getattr(mtoon1, "enabled", False):
                return True
    except Exception:
        pass

    # Check node tree for MToon group nodes
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


def extract_mtoon_params(material):
    """Extract parameters from an MToon material for the anime shader."""
    params = {
        "base_color": (1.0, 1.0, 1.0, 1.0),
        "base_color_texture": None,
        "normal_texture": None,
        "normal_strength": 1.0,
        "emissive_texture": None,
        "emissive_strength": 0.0,
        "shade_color": (0.35, 0.25, 0.40, 1.0),
        "alpha_mode": "OPAQUE",
        "alpha_cutoff": 0.5,
        "double_sided": False,
    }

    # Try VRM addon extension API (MToon 1.0)
    try:
        ext = getattr(material, "vrm_addon_extension", None)
        if ext is not None:
            mtoon1 = getattr(ext, "mtoon1", None)
            if mtoon1:
                pbr = getattr(mtoon1, "pbr_metallic_roughness", None)
                if pbr:
                    params["base_color"] = tuple(
                        getattr(pbr, "base_color_factor", (1.0, 1.0, 1.0, 1.0))
                    )
                    bct = getattr(pbr, "base_color_texture", None)
                    if bct:
                        src = getattr(bct, "index", None)
                        if src:
                            img = getattr(src, "source", None)
                            if img:
                                params["base_color_texture"] = img

                params["alpha_mode"] = getattr(mtoon1, "alpha_mode", "OPAQUE")
                params["double_sided"] = getattr(mtoon1, "double_sided", False)
                params["alpha_cutoff"] = getattr(mtoon1, "alpha_cutoff", 0.5)

                # Normal
                nt = getattr(mtoon1, "normal_texture", None)
                if nt:
                    ns = getattr(nt, "index", None)
                    if ns:
                        nimg = getattr(ns, "source", None)
                        if nimg:
                            params["normal_texture"] = nimg
                    params["normal_strength"] = getattr(nt, "scale", 1.0)

                # Emissive
                params["emissive_strength"] = getattr(mtoon1, "emissive_strength", 0.0)
                et = getattr(mtoon1, "emissive_texture", None)
                if et:
                    esrc = getattr(et, "index", None)
                    if esrc:
                        eimg = getattr(esrc, "source", None)
                        if eimg:
                            params["emissive_texture"] = eimg

                # MToon shade color
                mtoon_ext = getattr(mtoon1, "extensions", None)
                if mtoon_ext:
                    vm = getattr(mtoon_ext, "vrmc_materials_mtoon", None)
                    if vm:
                        sc = getattr(vm, "shade_color_factor", None)
                        if sc:
                            params["shade_color"] = (sc[0], sc[1], sc[2], 1.0)
                return params
    except Exception:
        pass

    # Try node tree extraction (legacy MToon 0.0 or fallback)
    try:
        if material.node_tree:
            for node in material.node_tree.nodes:
                if node.type == "GROUP" and node.node_tree:
                    nname = node.node_tree.name.lower()
                    if "mtoon" not in nname:
                        continue

                    # Try to find base color texture node
                    for inode in material.node_tree.nodes:
                        if inode.type == "TEX_IMAGE" and inode.image:
                            uname = inode.name.upper()
                            if "MAIN" in uname or "BASE" in uname or "DIFFUSE" in uname:
                                params["base_color_texture"] = inode.image
                                break
                            if "SHADE" in uname:
                                continue
                            if "NORMAL" in uname:
                                params["normal_texture"] = inode.image
                                continue
                            if "EMISSIVE" in uname or "EMIT" in uname:
                                params["emissive_texture"] = inode.image
                                continue
                            if "MATCAP" in uname or "RIM" in uname or "ANIMATION" in uname:
                                continue
                            if params["base_color_texture"] is None:
                                params["base_color_texture"] = inode.image
                    break
    except Exception:
        pass

    # Extract from Principled BSDF (fallback for non-MToon)
    if not params["base_color_texture"]:
        _extract_principled_params(material, params)

    return params


def _extract_principled_params(material, params):
    """Extract parameters from a Principled BSDF material."""
    try:
        if not material.node_tree:
            return
        for node in material.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                bc = node.inputs.get("Base Color")
                if bc and bc.is_linked:
                    for link in bc.links:
                        if link.from_node.type == "TEX_IMAGE":
                            params["base_color_texture"] = link.from_node.image
                            break
                elif bc:
                    params["base_color"] = tuple(bc.default_value)

                # Alpha
                alpha_in = node.inputs.get("Alpha")
                if alpha_in:
                    alpha_val = alpha_in.default_value
                    if alpha_val < 1.0:
                        params["alpha_mode"] = "BLEND"

                # Emission
                em = node.inputs.get("Emission Color")
                if em and em.is_linked:
                    for link in em.links:
                        if link.from_node.type == "TEX_IMAGE":
                            params["emissive_texture"] = link.from_node.image
                            break
                em_str = node.inputs.get("Emission Strength")
                if em_str:
                    params["emissive_strength"] = em_str.default_value

                # Normal
                nm = node.inputs.get("Normal")
                if nm and nm.is_linked:
                    for link in nm.links:
                        if link.from_node.type == "NORMAL_MAP":
                            params["normal_strength"] = link.from_node.inputs[
                                "Strength"
                            ].default_value
                            for nlink in link.from_node.inputs["Color"].links:
                                if nlink.from_node.type == "TEX_IMAGE":
                                    params["normal_texture"] = nlink.from_node.image
                                    break
                            break
                break
    except Exception:
        pass


# ============================================================
# MATERIAL CONVERSION
# ============================================================


def convert_material_to_anime(material, context, preset_name="anime_clean"):
    """Convert a single material to the anime shader, preserving existing textures."""
    if not material:
        return False

    if is_anime_shader_material(material):
        return True

    # Ensure node tree
    if not material.use_nodes:
        material.use_nodes = True

    tree = material.node_tree

    # Get or create shader group
    group = ensure_anime_shader_group(context)

    # Apply preset to group defaults
    apply_shader_preset(group, preset_name)

    # Find existing texture image nodes and keep them
    tex_nodes = []
    for node in tree.nodes:
        if node.type == "TEX_IMAGE":
            tex_nodes.append(node)

    # Find existing normal map nodes
    normal_map_node = None
    for node in tree.nodes:
        if node.type == "NORMAL_MAP":
            normal_map_node = node
            break

    # Find existing UV maps from the material
    uv_nodes = []
    for node in tree.nodes:
        if node.type == "UVMAP":
            uv_nodes.append(node)
        elif node.type == "TEX_COORD":
            uv_nodes.append(node)

    # Trace MToon group connections BEFORE removing nodes
    mtoon_tex_map = {}  # role → tex_node
    for node in tree.nodes:
        if node.type == "GROUP" and node.node_tree:
            nname = node.node_tree.name.lower()
            if "mtoon" in nname:
                for inp in node.inputs:
                    if inp.is_linked:
                        for link in inp.links:
                            fn = link.from_node
                            if fn.type == "TEX_IMAGE":
                                sn = inp.name.upper()
                                if "BASE" in sn or "MAIN" in sn or "COLOR" in sn:
                                    if "base" not in mtoon_tex_map:
                                        mtoon_tex_map["base"] = fn
                                elif "EMISSIVE" in sn or "EMIT" in sn:
                                    if "emissive" not in mtoon_tex_map:
                                        mtoon_tex_map["emissive"] = fn
                                elif "NORMAL" in sn:
                                    if "normal" not in mtoon_tex_map:
                                        mtoon_tex_map["normal"] = fn
                                elif "SHADE" in sn:
                                    if "shade" not in mtoon_tex_map:
                                        mtoon_tex_map["shade"] = fn
                            break

    # Helper: safely check if a node has a valid image (VRM addon may block .image access)
    def _has_valid_image(n):
        try:
            return n.image is not None and bool(n.image.name)
        except Exception:
            return False

    # Find main/base texture, normal texture, emissive texture
    # Priority: MToon connections → node name classification → sniff test
    main_tex = mtoon_tex_map.get("base")
    normal_tex = mtoon_tex_map.get("normal")
    emit_tex = mtoon_tex_map.get("emissive")
    other_tex = []

    if mtoon_tex_map.get("shade"):
        other_tex.append(mtoon_tex_map["shade"])

    for node in tex_nodes:
        name = node.name.upper()
        if normal_map_node and node in [
            l.from_node
            for l in tree.links
            if l.to_node == normal_map_node
        ]:
            if normal_tex is None:
                normal_tex = node
        elif "EMISSIVE" in name or "EMIT" in name:
            if emit_tex is None:
                emit_tex = node
        elif "NORMAL" in name and node != normal_tex:
            if normal_tex is None:
                normal_tex = node
        elif "SHADE" in name and node not in other_tex:
            other_tex.append(node)
        elif any(kw in name for kw in ("MATCAP", "OUTLINE", "RIM", "ANIMATION", "SHIFT")):
            pass
        elif "BASE" in name or "DIFFUSE" in name or "COLOR" in name:
            if main_tex is None:
                main_tex = node
        elif _has_valid_image(node):
            if main_tex is None:
                main_tex = node

    # Extract MToon params BEFORE removing nodes (needs MToon group to exist)
    params = extract_mtoon_params(material)

    # Remove all nodes except textures, uv maps, normal maps
    nodes_to_remove = []
    for node in tree.nodes:
        if node.type in {"TEX_IMAGE", "NORMAL_MAP", "UVMAP", "TEX_COORD", "MAPPING"}:
            continue
        nodes_to_remove.append(node)
    for node in nodes_to_remove:
        tree.nodes.remove(node)

    # Create the group node
    group_node = tree.nodes.new("ShaderNodeGroup")
    group_node.node_tree = group
    group_node.location = (0, 0)
    group_node.label = "VRM Anime Shader"

    # Create material output
    mat_output = tree.nodes.new("ShaderNodeOutputMaterial")
    mat_output.location = (300, 0)

    # Connect group to output
    tree.links.new(group_node.outputs["Surface"], mat_output.inputs["Surface"])

    # Connect main texture
    if main_tex:
        main_tex.location = (-600, 200)
        tree.links.new(main_tex.outputs["Color"], group_node.inputs["Base Color"])
        # Ensure UV is connected
        has_uv_link = any(
            l.from_node.type in {"UVMAP", "TEX_COORD"}
            for l in main_tex.inputs["Vector"].links
        )
        if not has_uv_link:
            uv = tree.nodes.new("ShaderNodeTexCoord")
            uv.location = (-1000, 200)
            tree.links.new(uv.outputs["UV"], main_tex.inputs["Vector"])
        # Connect Alpha for MASK/BLEND materials
        if params.get("alpha_mode") in ("MASK", "BLEND"):
            tree.links.new(main_tex.outputs["Alpha"], group_node.inputs["Alpha"])
    else:
        # Fallback: try to find any image texture in the material
        for node in tex_nodes:
            try:
                has_img = node.image is not None
            except Exception:
                has_img = False
            if has_img:
                node.location = (-600, 200)
                tree.links.new(node.outputs["Color"], group_node.inputs["Base Color"])
                has_uv_link = any(
                    l.from_node.type in {"UVMAP", "TEX_COORD"}
                    for l in node.inputs["Vector"].links
                )
                if not has_uv_link:
                    uv = tree.nodes.new("ShaderNodeTexCoord")
                    uv.location = (-1000, 200)
                    tree.links.new(uv.outputs["UV"], node.inputs["Vector"])
                if params.get("alpha_mode") in ("MASK", "BLEND"):
                    tree.links.new(node.outputs["Alpha"], group_node.inputs["Alpha"])
                break

    # Connect normal map if available
    if normal_map_node:
        normal_map_node.location = (-300, -200)
        if "Normal" in group_node.inputs:
            tree.links.new(
                normal_map_node.outputs["Normal"], group_node.inputs["Normal"]
            )
    elif normal_tex:
        nm_node = tree.nodes.new("ShaderNodeNormalMap")
        nm_node.location = (-300, -200)
        nm_node.inputs["Strength"].default_value = 1.0
        normal_tex.location = (-600, -200)
        tree.links.new(normal_tex.outputs["Color"], nm_node.inputs["Color"])
        if "Normal" in group_node.inputs:
            tree.links.new(nm_node.outputs["Normal"], group_node.inputs["Normal"])
        has_uv_link = any(
            l.from_node.type in {"UVMAP", "TEX_COORD"}
            for l in normal_tex.inputs["Vector"].links
        )
        if not has_uv_link:
            uv = tree.nodes.new("ShaderNodeTexCoord")
            uv.location = (-1000, -200)
            tree.links.new(uv.outputs["UV"], normal_tex.inputs["Vector"])

    # Connect emissive texture if available
    if emit_tex:
        emit_tex.location = (-600, -500)
        if "Emission Color" in group_node.inputs:
            tree.links.new(emit_tex.outputs["Color"], group_node.inputs["Emission Color"])
        group_node.inputs["Emission Strength"].default_value = params.get("emissive_strength", 0.0)
        has_uv_link = any(
            l.from_node.type in {"UVMAP", "TEX_COORD"}
            for l in emit_tex.inputs["Vector"].links
        )
        if not has_uv_link:
            uv = tree.nodes.new("ShaderNodeTexCoord")
            uv.location = (-1000, -500)
            tree.links.new(uv.outputs["UV"], emit_tex.inputs["Vector"])

    # Note: Shadow Color uses group interface default (from preset). No per-material
    # override — the Scene property UI syncs to all materials uniformly.

    # Set blend mode
    _set_blend_mode(material, params["alpha_mode"], params["alpha_cutoff"])

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
            material.alpha_threshold = alpha_cutoff

    return True


def convert_armature_materials(armature_obj, context, preset_name="anime_clean"):
    """Convert all materials on meshes parented to the given armature."""
    if not armature_obj or armature_obj.type != "ARMATURE":
        return 0, 0

    converted = 0
    skipped = 0
    converted_mats = set()

    # Find all mesh objects parented to this armature
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if obj.parent != armature_obj:
            continue

        for slot in obj.material_slots:
            mat = slot.material
            if not mat or mat.name in converted_mats:
                continue

            if is_anime_shader_material(mat):
                skipped += 1
                converted_mats.add(mat.name)
                continue

            if convert_material_to_anime(mat, context, preset_name):
                converted += 1
                converted_mats.add(mat.name)
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
        return (
            context.active_object is not None
            and context.active_object.type == "ARMATURE"
        )

    def execute(self, context):
        armature = context.active_object
        preset = context.scene.vas_props.preset
        converted, skipped = convert_armature_materials(armature, context, preset)

        if converted == 0 and skipped == 0:
            self.report(
                {"WARNING"},
                "No materials found on meshes parented to this armature",
            )
        elif converted > 0:
            self.report(
                {"INFO"},
                f"Converted {converted} material(s), skipped {skipped}",
            )
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
        return (
            context.active_object is not None
            and context.active_object.type == "ARMATURE"
        )

    def execute(self, context):
        armature = context.active_object
        preset_name = context.scene.vas_props.preset
        preset = PRESET_DEFAULTS.get(preset_name)
        if not preset:
            self.report({"ERROR"}, f"Preset '{preset_name}' not found")
            return {"CANCELLED"}

        # Update the shader group interface defaults
        group = bpy.data.node_groups.get(SHADER_GROUP_NAME)
        if group:
            apply_shader_preset(group, preset_name)

        # Update Scene properties (triggers sync to all materials via update callbacks)
        props = context.scene.vas_props
        prop_map = {
            "shadow_color": "shadow_color",
            "shadow_threshold": "shadow_threshold",
            "shadow_smoothness": "shadow_smoothness",
            "rim_color": "rim_color",
            "rim_strength": "rim_strength",
            "rim_threshold": "rim_threshold",
            "specular_color": "specular_color",
            "specular_strength": "specular_strength",
            "specular_smoothness": "specular_smoothness",
            "shadow_tint_strength": "shadow_tint_strength",
            "saturation": "saturation",
            "brightness": "brightness",
            "emission_strength": "emission_strength",
        }
        for attr, pkey in prop_map.items():
            if pkey in preset and hasattr(props, attr):
                try:
                    setattr(props, attr, preset[pkey])
                except Exception:
                    pass

        self.report(
            {"INFO"}, f"Applied preset '{preset['label']}' to all materials"
        )
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

        # Update shader group
        group = bpy.data.node_groups.get(SHADER_GROUP_NAME)
        if group:
            apply_shader_preset(group, self.preset_name)

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
            # Unregister if registered
            try:
                unregister()
            except Exception:
                pass

            # Re-import
            importlib.reload(mod)

            # Re-register
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
    """Push a shader param value to ALL anime shader materials."""
    # Map Scene property name → socket name
    socket_name = {
        "shadow_color": "Shadow Color",
        "shadow_threshold": "Shadow Threshold",
        "shadow_smoothness": "Shadow Smoothness",
        "shadow_tint_strength": "Shadow Tint Strength",
        "rim_color": "Rim Color",
        "rim_strength": "Rim Strength",
        "rim_threshold": "Rim Threshold",
        "specular_color": "Specular Color",
        "specular_strength": "Specular Strength",
        "specular_smoothness": "Specular Smoothness",
        "saturation": "Saturation",
        "brightness": "Brightness",
        "emission_strength": "Emission Strength",
    }.get(prop_name, prop_name)
    # Convert bpy_prop_array to tuple if needed
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
    """Create an update callback that syncs to all materials."""
    def update_fn(self, context):
        value = getattr(self, param_name)
        _sync_param_to_all(param_name, value)
    return update_fn


class VAS_Properties(PropertyGroup):
    preset: EnumProperty(
        name="Shader Preset",
        description="Select an anime shader preset",
        items=[
            (k, v["label"], f"Apply {v['label']} style preset")
            for k, v in PRESET_DEFAULTS.items()
        ],
        default="anime_clean",
    )

    # Shader parameters (synced to all materials automatically)
    shadow_color: bpy.props.FloatVectorProperty(
        name="Shadow Color", subtype="COLOR", size=4,
        default=(0.35, 0.25, 0.40, 1.0),
        update=_make_update("shadow_color"),
    )
    shadow_threshold: bpy.props.FloatProperty(
        name="Shadow Threshold", default=0.42, min=0.0, max=1.0, subtype="FACTOR",
        update=_make_update("shadow_threshold"),
    )
    shadow_smoothness: bpy.props.FloatProperty(
        name="Shadow Smoothness", default=0.03, min=0.0, max=0.5,
        update=_make_update("shadow_smoothness"),
    )
    shadow_tint_strength: bpy.props.FloatProperty(
        name="Shadow Tint Strength", default=0.5, min=0.0, max=1.0, subtype="FACTOR",
        update=_make_update("shadow_tint_strength"),
    )
    rim_color: bpy.props.FloatVectorProperty(
        name="Rim Color", subtype="COLOR", size=4,
        default=(0.85, 0.85, 0.95, 1.0),
        update=_make_update("rim_color"),
    )
    rim_strength: bpy.props.FloatProperty(
        name="Rim Strength", default=0.6, min=0.0, max=2.0,
        update=_make_update("rim_strength"),
    )
    rim_threshold: bpy.props.FloatProperty(
        name="Rim Threshold", default=0.65, min=0.0, max=1.0, subtype="FACTOR",
        update=_make_update("rim_threshold"),
    )
    specular_color: bpy.props.FloatVectorProperty(
        name="Specular Color", subtype="COLOR", size=4,
        default=(1.0, 1.0, 1.0, 1.0),
        update=_make_update("specular_color"),
    )
    specular_strength: bpy.props.FloatProperty(
        name="Specular Strength", default=0.35, min=0.0, max=2.0,
        update=_make_update("specular_strength"),
    )
    specular_smoothness: bpy.props.FloatProperty(
        name="Specular Smoothness", default=0.18, min=0.0, max=1.0,
        update=_make_update("specular_smoothness"),
    )
    saturation: bpy.props.FloatProperty(
        name="Saturation", default=1.1, min=0.0, max=2.0,
        update=_make_update("saturation"),
    )
    brightness: bpy.props.FloatProperty(
        name="Brightness", default=1.0, min=0.0, max=2.0,
        update=_make_update("brightness"),
    )
    emission_strength: bpy.props.FloatProperty(
        name="Emission Strength", default=0.0, min=0.0, max=10.0,
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

        # --- Top Bar: Reload + Rebuild ---
        row = layout.row(align=True)
        row.operator("vas.reload_addon", text="Reload", icon="FILE_REFRESH")
        row.operator("vas.rebuild_shader", text="Rebuild Shader", icon="MODIFIER")

        # --- Conversion Section ---
        box = layout.box()
        box.label(text="Material Conversion", icon="MATERIAL")
        row = box.row(align=True)
        if obj and obj.type == "ARMATURE":
            row.operator("vas.convert_mtoon", icon="PLAY")
        else:
            sub = row.row(align=True)
            sub.operator("vas.convert_mtoon", icon="PLAY")
            sub.enabled = False

        # Info text
        if obj and obj.type == "ARMATURE":
            mesh_count = sum(
                1 for o in bpy.data.objects if o.type == "MESH" and o.parent == obj
            )
            anime_count = 0
            mtoon_count = 0
            for o in bpy.data.objects:
                if o.type != "MESH" or o.parent != obj:
                    continue
                for slot in o.material_slots:
                    mat = slot.material
                    if mat:
                        if is_anime_shader_material(mat):
                            anime_count += 1
                        elif is_mtoon_material(mat):
                            mtoon_count += 1
            box.label(
                text=f"Meshes: {mesh_count} | Anime: {anime_count} | MToon: {mtoon_count}",
                icon="INFO",
            )
        elif obj:
            box.label(text=f"Selected: {obj.name} (not armature)", icon="ERROR")
        else:
            box.label(text="Select an armature", icon="INFO")

        # --- Preset Section ---
        box = layout.box()
        box.label(text="Shader Presets", icon="PRESET")
        box.prop(context.scene.vas_props, "preset", text="")

        row = box.row(align=True)
        row.operator("vas.apply_preset", icon="CHECKMARK")

        # Preset buttons grid
        col = box.column(align=True)
        for key, preset in PRESET_DEFAULTS.items():
            row = col.row(align=True)
            op = row.operator(
                "vas.switch_preset",
                text=preset["label"],
                icon="SHADING_SOLID"
                if key == context.scene.vas_props.preset
                else "NONE",
            )
            op.preset_name = key

        # --- Shader Controls Section ---
        box = layout.box()
        box.label(text="Shader Parameters", icon="PREFERENCES")

        group = bpy.data.node_groups.get(SHADER_GROUP_NAME)
        if not group:
            box.label(text="No shader group found", icon="ERROR")
            return

        # Find material with this shader
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

        # Load current values from the first material's group node into Scene props
        def _reload_scene_props():
            props = context.scene.vas_props
            for node in active_mat.node_tree.nodes:
                if node.type == "GROUP" and node.node_tree and node.node_tree.name == SHADER_GROUP_NAME:
                    for inp in node.inputs:
                        name = inp.name.lower().replace(" ", "_")
                        if hasattr(props, name):
                            try:
                                setattr(props, name, inp.default_value)
                            except Exception:
                                pass
                    break
        _reload_scene_props()

        # Draw shader parameters from Scene props (auto-syncs to all materials)
        self._draw_shader_params(box, context)

    def _draw_shader_params(self, box, context):
        """Draw adjustable parameters from Scene properties (syncs to all materials)."""
        col = box.column(align=True)
        props = context.scene.vas_props

        def safe_prop(box, attr, label, icon=None):
            """Draw a Scene property if the attribute exists."""
            if not hasattr(props, attr):
                row = box.row()
                row.label(text=f"{label}: (rebuild shader)", icon="ERROR")
                return
            box.prop(props, attr, text=label)

        # Shadow
        sub = col.box()
        sub.label(text="Shadow", icon="SHADING_RENDERED")
        safe_prop(sub, "shadow_color", "Color")
        safe_prop(sub, "shadow_threshold", "Threshold")
        safe_prop(sub, "shadow_smoothness", "Smoothness")
        safe_prop(sub, "shadow_tint_strength", "Tint Strength")

        # Rim Light
        sub = col.box()
        sub.label(text="Rim Light", icon="LIGHT_SUN")
        safe_prop(sub, "rim_color", "Color")
        safe_prop(sub, "rim_strength", "Strength")
        safe_prop(sub, "rim_threshold", "Threshold")

        # Specular
        sub = col.box()
        sub.label(text="Specular", icon="LIGHT")
        safe_prop(sub, "specular_color", "Color")
        safe_prop(sub, "specular_strength", "Strength")
        safe_prop(sub, "specular_smoothness", "Smoothness")

        # Color Adjustments
        sub = col.box()
        sub.label(text="Color Adjust", icon="COLOR")
        safe_prop(sub, "saturation", "Saturation")
        safe_prop(sub, "brightness", "Brightness")

        # Emission
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

            for i, slot in enumerate(mesh_obj.material_slots):
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

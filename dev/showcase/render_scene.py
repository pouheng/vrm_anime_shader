"""Headless Blender comparison harness for VRM Anime Shader (v2).

Imports a VRM twice at the same location, converts the second copy with the
addon, then renders each copy separately with identical camera/lighting so the
two images can be composited side by side pixel-for-pixel.

Usage:
  blender -b --factory-startup --python render_scene.py -- \
      --vrm "model.vrm" --out out/xxx --tag baseline \
      --view full|upper|face --light studio|sunset|sky|night|color \
      --preset anime_clean --res 1200x800 --samples 32 [--no-outline]
      [--mode both|orig|conv] [--only-anime]
"""
import bpy
import math
import os
import sys
import traceback
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def get_arg(name, default=None):
    for i, a in enumerate(ARGS):
        if a == "--" + name:
            return ARGS[i + 1]
    return default


def flag(name):
    return "--" + name in ARGS


VRM = get_arg("vrm")
OUT_DIR = get_arg("out", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out"))
TAG = get_arg("tag", "test")
VIEW = get_arg("view", "full")
LIGHT = get_arg("light", "studio")
PRESET = get_arg("preset", "anime_clean")
RES = get_arg("res", "1200x800")
SAMPLES = int(get_arg("samples", "32"))
MODE = get_arg("mode", "both")  # both | orig | conv
OUTLINE = not flag("no-outline")
GROUND = flag("ground")
CONVERT_ADDON = get_arg("convert-addon")


def log(*a):
    print("[LAB]", *a, flush=True)


def enable_addons():
    for name in ("bl_ext.user_default.vrm", "vrm_anime_shader"):
        try:
            bpy.ops.preferences.addon_enable(module=name)
            log("enabled", name)
        except Exception as e:
            log("ENABLE_FAIL", name, repr(e))


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.users == 0:
            bpy.data.collections.remove(c)


def import_vrm(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.vrm(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next((o for o in new if o.type == "ARMATURE"), None)
    meshes = [o for o in new if o.type == "MESH"]
    log("imported armature", arm.name if arm else None, "meshes", len(meshes), "new", len(new))
    return {"arm": arm, "meshes": meshes, "objects": new}


def render_objects(model):
    """All objects that should be hidden/shown for a render pass."""
    return [o for o in model["objects"] if o.type in ("MESH", "CURVE", "SURFACE", "META", "FONT")]


def set_model_visible(model, visible):
    for o in render_objects(model):
        o.hide_render = not visible


def bbox_of(objects):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    deps = bpy.context.evaluated_depsgraph_get()
    for o in objects:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(deps)
        try:
            for corner in ev.bound_box:
                wc = ev.matrix_world @ Vector(corner)
                mn.x, mn.y, mn.z = min(mn.x, wc.x), min(mn.y, wc.y), min(mn.z, wc.z)
                mx.x, mx.y, mx.z = max(mx.x, wc.x), max(mx.y, wc.y), max(mx.z, wc.z)
        except Exception:
            pass
    return mn, mx


# ---------------------------------------------------------------- lighting


def setup_world(mode):
    world = bpy.data.worlds.get("LabWorld") or bpy.data.worlds.new("LabWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(bg.outputs[0], out.inputs["Surface"])

    if mode in ("sunset", "sky", "outdoor"):
        sky = nt.nodes.new("ShaderNodeTexSky")
        sky.sky_type = "NISHITA"
        if mode == "sunset":
            sky.sun_elevation = math.radians(8)
            sky.sun_rotation = math.radians(140)
            sky.air_density = 2.5
            sky.dust_density = 6.0
            sky.sun_intensity = 1.0
            bg.inputs["Strength"].default_value = 0.45
        elif mode == "outdoor":
            sky.sun_elevation = math.radians(24)
            sky.sun_rotation = math.radians(125)
            sky.air_density = 1.2
            sky.dust_density = 2.5
            sky.sun_intensity = 1.0
            bg.inputs["Strength"].default_value = 0.18
        else:
            sky.sun_elevation = math.radians(35)
            sky.sun_rotation = math.radians(120)
            sky.air_density = 1.0
            sky.dust_density = 1.5
            bg.inputs["Strength"].default_value = 0.6
        nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    elif mode == "night":
        bg.inputs["Color"].default_value = (0.012, 0.02, 0.05, 1)
        bg.inputs["Strength"].default_value = 1.0
    elif mode == "color":
        bg.inputs["Color"].default_value = (0.015, 0.015, 0.02, 1)
    elif mode == "world":
        bg.inputs["Color"].default_value = (0.22, 0.25, 0.32, 1)
        bg.inputs["Strength"].default_value = 1.0
    else:  # studio
        bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
        bg.inputs["Strength"].default_value = 1.0
    return world


def add_area(name, loc, energy, color, size=2.0, shape="DISK"):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = shape
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    return obj


def aim_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_lights(mode, center, height):
    lights = []
    if mode == "studio":
        key = add_area("Key", (-2.2, -2.6, height * 0.85), 500, (1.0, 0.96, 0.9), 2.5)
        aim_at(key, center)
        fill = add_area("Fill", (2.6, -2.0, height * 0.6), 160, (0.75, 0.85, 1.0), 3.0)
        aim_at(fill, center)
        rim = add_area("Rim", (0.8, 3.0, height * 0.95), 450, (0.9, 0.95, 1.0), 1.6)
        aim_at(rim, center)
        lights += [key, fill, rim]
    elif mode in ("sunset", "sky", "night", "outdoor"):
        sun_data = bpy.data.lights.new("Sun", "SUN")
        sun = bpy.data.objects.new("Sun", sun_data)
        bpy.context.scene.collection.objects.link(sun)
        if mode == "sunset":
            sun_data.energy = 4.0
            sun_data.color = (1.0, 0.62, 0.38)
            sun_data.angle = math.radians(2.0)
            sun.rotation_euler = (math.radians(80), 0, math.radians(-40))
        elif mode == "outdoor":
            sun_data.energy = 3.0
            sun_data.color = (1.0, 0.92, 0.80)
            sun_data.angle = math.radians(2.5)
            sun.rotation_euler = (math.radians(62), 0, math.radians(-38))
        elif mode == "sky":
            sun_data.energy = 3.0
            sun_data.color = (1.0, 0.95, 0.9)
            sun_data.angle = math.radians(1.5)
            sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
        else:
            sun_data.energy = 0.15
            sun_data.color = (0.55, 0.7, 1.0)
            sun.rotation_euler = (math.radians(65), 0, math.radians(20))
        lights.append(sun)
        if mode == "night":
            p1 = bpy.data.lights.new("WarmPoint", "POINT")
            p1.energy = 60
            p1.color = (1.0, 0.72, 0.45)
            p1.shadow_soft_size = 0.3
            o1 = bpy.data.objects.new("WarmPoint", p1)
            bpy.context.scene.collection.objects.link(o1)
            o1.location = (center[0] - 0.8, center[1] - 1.2, center[2] + 0.5)
            p2 = bpy.data.lights.new("CoolPoint", "POINT")
            p2.energy = 50
            p2.color = (0.4, 0.6, 1.0)
            p2.shadow_soft_size = 0.4
            o2 = bpy.data.objects.new("CoolPoint", p2)
            bpy.context.scene.collection.objects.link(o2)
            o2.location = (center[0] + 1.0, center[1] + 0.6, center[2] + 0.8)
            lights += [o1, o2]
    elif mode == "color":
        l1 = add_area("Magenta", (-2.5, -2.0, height * 0.8), 550, (1.0, 0.1, 0.55), 2.0)
        aim_at(l1, center)
        l2 = add_area("Cyan", (2.5, -2.0, height * 0.8), 550, (0.1, 0.85, 1.0), 2.0)
        aim_at(l2, center)
        l3 = add_area("Back", (0, 2.5, height * 1.0), 400, (0.4, 0.4, 1.0), 2.0)
        aim_at(l3, center)
        lights += [l1, l2, l3]
    return lights


def head_anchor(arm):
    """Return (top_z, head_length) from the armature's head bone if present."""
    try:
        bones = arm.data.bones
        head = None
        for b in bones:
            n = b.name.lower()
            if "head" in n and "eye" not in n and "jaw" not in n and "neck" not in n:
                head = b
                break
        if head is None:
            return None
        mw = arm.matrix_world
        head_pos = mw @ head.head_local
        tail_pos = mw @ head.tail_local
        top_z = max(head_pos.z, tail_pos.z)
        length = (tail_pos - head_pos).length
        return (top_z, max(length, 0.05))
    except Exception:
        return None


def add_ground(center):
    bpy.ops.mesh.primitive_plane_add(size=30, location=(center[0], center[1], 0.0))
    plane = bpy.context.active_object
    plane.name = "LabGround"
    mat = bpy.data.materials.get("LabGround") or bpy.data.materials.new("LabGround")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.16, 0.16, 0.17, 1)
        bsdf.inputs["Roughness"].default_value = 0.75
    plane.data.materials.append(mat)
    return plane


# ---------------------------------------------------------------- camera


def setup_camera(view, center, size, head=None):
    cam_data = bpy.data.cameras.new("LabCam")
    cam = bpy.data.objects.new("LabCam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam_data.type = "ORTHO"
    cam_data.sensor_fit = "HORIZONTAL"

    res_x, res_y = [int(x) for x in RES.split("x")]
    aspect = res_x / res_y

    if view == "full":
        cam_data.ortho_scale = max(size.x * 1.08, size.z * 1.08 * aspect)
        z = center[2]
    elif view == "upper":
        top = head[0] if head else center[2] + size.z * 0.5
        cam_data.ortho_scale = max(size.x * 0.62, (top - center[2]) * 1.15 * aspect)
        z = center[2] + (top - center[2]) * 0.55
    elif view == "face":
        if head:
            top, hlen = head
            cam_data.ortho_scale = max(hlen * 2.6 * aspect, 0.24)
            z = top - hlen * 1.15
        else:
            cam_data.ortho_scale = max(0.30, size.z * 0.24 * aspect)
            z = center[2] + size.z * 0.395
    else:
        raise ValueError(view)
    cam.location = (center[0], center[1] - max(5.0, size.z * 4.0), z)
    cam.rotation_euler = (math.radians(90), 0, 0)
    return cam


# ---------------------------------------------------------------- render


def configure_render():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    res_x, res_y = [int(x) for x in RES.split("x")]
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.view_settings.use_curve_mapping = False
    ee = scene.eevee
    ee.taa_render_samples = SAMPLES
    try:
        ee.use_raytracing = True
        ee.ray_tracing_options.resolution_scale = "1"
    except Exception:
        pass
    try:
        ee.use_shadows = True
    except Exception:
        pass


def render_to(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    log("rendered", path)


def main():
    log("args", ARGS)
    enable_addons()
    clear_scene()
    if not VRM or not os.path.exists(VRM):
        raise SystemExit("VRM not found: " + str(VRM))

    model_a = import_vrm(VRM)  # original MToon
    model_b = None
    if MODE in ("both", "conv"):
        model_b = import_vrm(VRM)  # will be converted

    # hide second while measuring first
    if model_b:
        set_model_visible(model_b, False)
    bpy.context.view_layer.update()

    mn, mx = bbox_of(model_a["meshes"])
    size = mx - mn
    center = (mn + mx) / 2
    log("bbox", tuple(round(v, 3) for v in mn), tuple(round(v, 3) for v in mx))

    setup_world(LIGHT)
    setup_lights(LIGHT, center, size.z)

    if not OUTLINE:
        for o in bpy.data.objects:
            if o.type == "MESH":
                for m in list(o.modifiers):
                    try:
                        if m.type == "NODES" and m.node_group and "Outline" in m.node_group.name:
                            o.modifiers.remove(m)
                    except Exception:
                        pass

    if model_b:
        if CONVERT_ADDON:
            import importlib.util

            spec = importlib.util.spec_from_file_location("vas_custom", CONVERT_ADDON)
            vas = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(vas)
        else:
            import vrm_anime_shader as vas

        bpy.context.view_layer.objects.active = model_b["arm"]
        for o in bpy.context.selected_objects:
            o.select_set(False)
        model_b["arm"].select_set(True)
        converted, skipped = vas.convert_armature_materials(model_b["arm"], bpy.context, PRESET)
        log("converted", converted, "skipped", skipped)
        missing = []
        for obj in model_b["meshes"]:
            for slot in obj.material_slots:
                if slot.material and not vas.is_anime_shader_material(slot.material):
                    missing.append((obj.name, slot.material.name))
        if missing:
            log("NOT_CONVERTED", missing)
        group = bpy.data.node_groups.get(vas.SHADER_GROUP_NAME)
        log("group", group.name if group else None, "nodes", len(group.nodes) if group else 0)

    setup_camera(VIEW, center, size, head=head_anchor(model_a["arm"]))
    if GROUND:
        add_ground(center)
    configure_render()
    bpy.context.view_layer.update()

    base = os.path.join(OUT_DIR, f"{TAG}_{VIEW}_{LIGHT}")

    if MODE in ("both", "orig"):
        set_model_visible(model_a, True)
        if model_b:
            set_model_visible(model_b, False)
        bpy.context.view_layer.update()
        render_to(base + "_orig.png")

    if MODE in ("both", "conv"):
        set_model_visible(model_a, False)
        set_model_visible(model_b, True)
        bpy.context.view_layer.update()
        render_to(base + "_conv.png")

    log("DONE", base)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

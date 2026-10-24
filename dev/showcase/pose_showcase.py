"""Pose the VRM character and render showcase images of the anime shader.

Usage:
  blender -b --factory-startup --python pose_showcase.py -- \
      --vrm model.vrm --out out/showcase_pose --pose idle \
      --light studio|outdoor|sunset|night|color --preset anime_clean \
      --res 1000x1400 --samples 64 [--mode conv|both] [--yaw 22] [--tag name]
"""
import bpy
import math
import os
import sys
import traceback
from mathutils import Matrix, Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import render_scene as rs  # noqa: E402

ARGS = rs.ARGS
VRM = rs.get_arg("vrm")
OUT_DIR = rs.get_arg("out", os.path.join(os.path.dirname(SCRIPT_DIR), "out", "showcase_pose"))
POSE = rs.get_arg("pose", "idle")
LIGHT = rs.get_arg("light", "studio")
PRESET = rs.get_arg("preset", "anime_clean")
RES = rs.get_arg("res", "1000x1400")
SAMPLES = int(rs.get_arg("samples", "48"))
MODE = rs.get_arg("mode", "conv")  # conv | both
YAW = float(rs.get_arg("yaw", "22"))
TAG = rs.get_arg("tag", POSE)
FRAMING = float(rs.get_arg("framing", "1.32"))
FRAME = rs.get_arg("frame", "full")  # full | upper | portrait
PARAMS_FILE = rs.get_arg("params")


# ---------------------------------------------------------------- posing


def aim_bone(pbone, direction):
    """Aim a pose bone along an armature-space direction, keeping its head."""
    target = Vector(direction).normalized()
    current = (pbone.tail - pbone.head).normalized()
    rot = current.rotation_difference(target).to_matrix().to_4x4()
    head = pbone.head.copy()
    pbone.matrix = Matrix.Translation(head) @ rot @ Matrix.Translation(-head) @ pbone.matrix
    bpy.context.view_layer.update()


def rotate_bone(pbone, axis, degrees):
    """Rotate a pose bone around its head about an armature-space axis."""
    rot = Matrix.Rotation(math.radians(degrees), 4, axis)
    head = pbone.head.copy()
    pbone.matrix = Matrix.Translation(head) @ rot @ Matrix.Translation(-head) @ pbone.matrix
    bpy.context.view_layer.update()


def apply_ops(arm, ops):
    bones = arm.pose.bones
    for op in ops:
        kind = op[0]
        pbone = bones.get(op[1])
        if not pbone:
            print("[POSE] missing bone", op[1], flush=True)
            continue
        if kind == "aim":
            aim_bone(pbone, op[2])
        elif kind == "rot":
            rotate_bone(pbone, op[2], op[3])
        elif kind == "rot_loc":  # rotate in bone local space (rare)
            pbone.rotation_mode = "XYZ"
            pbone.rotation_euler = [math.radians(v) for v in op[2]]
            bpy.context.view_layer.update()


POSES = {
    "idle": [
        ("rot", "J_Bip_C_Hips", "Y", 3.0),
        ("aim", "J_Bip_C_Spine", (0.04, -0.01, 1.0)),
        ("aim", "J_Bip_C_Chest", (0.03, 0.03, 1.0)),
        ("aim", "J_Bip_C_UpperChest", (0.01, 0.06, 1.0)),
        ("aim", "J_Bip_C_Neck", (0.0, 0.02, 1.0)),
        ("aim", "J_Bip_C_Head", (0.10, -0.03, 1.0)),
        ("aim", "J_Bip_L_Shoulder", (0.98, 0.02, -0.20)),
        ("aim", "J_Bip_L_UpperArm", (0.32, 0.03, -1.0)),
        ("aim", "J_Bip_L_LowerArm", (0.20, -0.16, -1.0)),
        ("aim", "J_Bip_L_Hand", (0.16, -0.28, -1.0)),
        ("aim", "J_Bip_R_Shoulder", (-0.98, 0.02, -0.20)),
        ("aim", "J_Bip_R_UpperArm", (-0.28, 0.03, -1.0)),
        ("aim", "J_Bip_R_LowerArm", (-0.16, -0.18, -1.0)),
        ("aim", "J_Bip_R_Hand", (-0.12, -0.30, -1.0)),
        ("aim", "J_Bip_L_UpperLeg", (0.04, 0.02, -1.0)),
        ("aim", "J_Bip_L_LowerLeg", (0.02, 0.06, -1.0)),
        ("aim", "J_Bip_R_UpperLeg", (-0.06, 0.02, -1.0)),
        ("aim", "J_Bip_R_LowerLeg", (-0.03, 0.05, -1.0)),
    ],
    "wave": [
        ("rot", "J_Bip_C_Hips", "Y", -4.0),
        ("aim", "J_Bip_C_Spine", (-0.06, -0.01, 1.0)),
        ("aim", "J_Bip_C_Chest", (-0.05, 0.03, 1.0)),
        ("aim", "J_Bip_C_UpperChest", (-0.03, 0.06, 1.0)),
        ("aim", "J_Bip_C_Neck", (-0.02, 0.02, 1.0)),
        ("aim", "J_Bip_C_Head", (-0.12, -0.02, 1.0)),
        ("aim", "J_Bip_L_Shoulder", (0.98, 0.02, -0.15)),
        ("aim", "J_Bip_L_UpperArm", (0.62, 0.06, -0.78)),
        ("aim", "J_Bip_L_LowerArm", (-0.18, -0.62, -0.55)),
        ("aim", "J_Bip_L_Hand", (-0.35, -0.80, -0.30)),
        ("aim", "J_Bip_R_Shoulder", (-0.95, 0.02, 0.15)),
        ("aim", "J_Bip_R_UpperArm", (-0.62, 0.05, 0.78)),
        ("aim", "J_Bip_R_LowerArm", (0.05, -0.05, 1.0)),
        ("aim", "J_Bip_R_Hand", (0.25, -0.25, 1.0)),
        ("aim", "J_Bip_L_UpperLeg", (0.05, 0.02, -1.0)),
        ("aim", "J_Bip_L_LowerLeg", (0.02, 0.05, -1.0)),
        ("aim", "J_Bip_R_UpperLeg", (-0.07, 0.02, -1.0)),
        ("aim", "J_Bip_R_LowerLeg", (-0.03, 0.05, -1.0)),
    ],
    "point": [
        ("rot", "J_Bip_C_Hips", "Y", 6.0),
        ("rot", "J_Bip_C_Hips", "Z", -8.0),
        ("aim", "J_Bip_C_Spine", (0.02, -0.02, 1.0)),
        ("aim", "J_Bip_C_Chest", (0.0, 0.04, 1.0)),
        ("aim", "J_Bip_C_UpperChest", (-0.02, 0.08, 1.0)),
        ("aim", "J_Bip_C_Neck", (0.0, 0.04, 1.0)),
        ("aim", "J_Bip_C_Head", (0.02, -0.10, 1.0)),
        ("aim", "J_Bip_L_Shoulder", (0.90, 0.05, -0.30)),
        ("aim", "J_Bip_L_UpperArm", (0.30, 0.10, -1.0)),
        ("aim", "J_Bip_L_LowerArm", (0.10, -0.35, -0.95)),
        ("aim", "J_Bip_L_Hand", (0.05, -0.45, -0.90)),
        ("aim", "J_Bip_R_Shoulder", (-0.98, 0.05, 0.05)),
        ("aim", "J_Bip_R_UpperArm", (-0.22, -0.86, 0.30)),
        ("aim", "J_Bip_R_LowerArm", (-0.10, -0.98, 0.10)),
        ("aim", "J_Bip_R_Hand", (-0.05, -1.0, 0.05)),
        ("aim", "J_Bip_L_UpperLeg", (0.16, 0.05, -1.0)),
        ("aim", "J_Bip_L_LowerLeg", (0.08, 0.05, -1.0)),
        ("aim", "J_Bip_R_UpperLeg", (-0.16, 0.04, -1.0)),
        ("aim", "J_Bip_R_LowerLeg", (-0.08, 0.05, -1.0)),
    ],
    "lookback": [
        ("rot", "J_Bip_C_Hips", "Z", 25.0),
        ("rot", "J_Bip_C_Spine", "Z", 8.0),
        ("rot", "J_Bip_C_Chest", "Z", 8.0),
        ("rot", "J_Bip_C_UpperChest", "Z", 8.0),
        ("rot", "J_Bip_C_Neck", "Z", 12.0),
        ("rot", "J_Bip_C_Head", "Z", 16.0),
        ("rot", "J_Bip_C_Head", "Y", 6.0),
        ("aim", "J_Bip_L_Shoulder", (0.98, 0.04, -0.16)),
        ("aim", "J_Bip_L_UpperArm", (0.30, 0.08, -1.0)),
        ("aim", "J_Bip_L_LowerArm", (0.18, -0.20, -1.0)),
        ("aim", "J_Bip_L_Hand", (0.12, -0.30, -1.0)),
        ("aim", "J_Bip_R_Shoulder", (-0.98, 0.04, -0.16)),
        ("aim", "J_Bip_R_UpperArm", (-0.36, 0.12, -0.96)),
        ("aim", "J_Bip_R_LowerArm", (-0.48, -0.45, -0.75)),
        ("aim", "J_Bip_R_Hand", (-0.55, -0.70, -0.60)),
        ("aim", "J_Bip_L_UpperLeg", (0.07, 0.02, -1.0)),
        ("aim", "J_Bip_L_LowerLeg", (0.02, 0.05, -1.0)),
        ("aim", "J_Bip_R_UpperLeg", (-0.10, 0.03, -1.0)),
        ("aim", "J_Bip_R_LowerLeg", (-0.05, 0.06, -1.0)),
    ],
}


# ---------------------------------------------------------------- scene


def setup_backdrop(center, mode):
    bpy.ops.mesh.primitive_plane_add(size=40, location=(center[0], center[1], 0.0))
    ground = bpy.context.active_object
    ground.name = "ShowcaseGround"
    mat = bpy.data.materials.new("ShowcaseGround")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf:
        if mode == "color":
            bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1)
            bsdf.inputs["Roughness"].default_value = 0.18
        elif mode in ("outdoor", "sunset"):
            bsdf.inputs["Base Color"].default_value = (0.20, 0.19, 0.17, 1)
            bsdf.inputs["Roughness"].default_value = 0.55
        else:
            bsdf.inputs["Base Color"].default_value = (0.055, 0.055, 0.065, 1)
            bsdf.inputs["Roughness"].default_value = 0.22
    ground.data.materials.append(mat)
    return ground


def setup_showcase_world(mode):
    if mode in ("outdoor", "sunset"):
        world = rs.setup_world(mode)
        if mode == "sunset":
            # keep the Nishita gradient readable instead of clipping to yellow
            for node in world.node_tree.nodes:
                if node.bl_idname == "ShaderNodeBackground":
                    node.inputs["Strength"].default_value *= 0.32
        return world
    world = bpy.data.worlds.new("ShowcaseWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    if mode == "color":
        bg.inputs["Color"].default_value = (0.008, 0.008, 0.012, 1)
    elif mode == "night":
        bg.inputs["Color"].default_value = (0.01, 0.015, 0.04, 1)
    else:
        bg.inputs["Color"].default_value = (0.02, 0.021, 0.028, 1)
    bg.inputs["Strength"].default_value = 1.0


def setup_showcase_lights(mode, center, height):
    rs.setup_lights(mode, center, height)


def setup_showcase_camera(center, size, yaw_deg, head=None):
    cam_data = bpy.data.cameras.new("ShowcaseCam")
    cam = bpy.data.objects.new("ShowcaseCam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam_data.lens = 62
    cam_data.sensor_width = 36

    if FRAME == "upper":
        frame_height = size.z * 0.58
        target_z = center[2] + size.z * 0.24
    elif FRAME == "portrait" and head:
        frame_height = max(head[1] * 3.2, 0.35)
        target_z = head[0] - head[1] * 0.75
        cam_data.lens = 78
    elif FRAME == "portrait":
        frame_height = size.z * 0.30
        target_z = center[2] + size.z * 0.34
        cam_data.lens = 78
    else:
        frame_height = size.z
        target_z = center[2] + size.z * 0.02

    res_x, res_y = [int(x) for x in RES.split("x")]
    aspect = res_x / res_y
    hfov = 2 * math.atan(cam_data.sensor_width / (2 * cam_data.lens))
    vfov = 2 * math.atan(math.tan(hfov / 2) / aspect)
    target = Vector((center[0], center[1], target_z))
    dist = (frame_height * FRAMING / 2) / math.tan(vfov / 2) + size.y * 0.6
    yaw = math.radians(yaw_deg)
    cam.location = (
        target.x + math.sin(yaw) * dist,
        target.y - math.cos(yaw) * dist,
        target.z + frame_height * 0.06,
    )
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return cam


def configure_quality():
    rs.configure_render()
    scene = bpy.context.scene
    scene.eevee.taa_render_samples = SAMPLES
    try:
        scene.eevee.use_raytracing = True
        scene.eevee.ray_tracing_options.resolution_scale = "1"
        scene.eevee.ray_tracing_options.trace_max_roughness = 0.8
    except Exception:
        pass
    # subtle bloom via compositor glare for neon shots
    if LIGHT == "color":
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        rl = tree.nodes.new("CompositorNodeRLayers")
        glare = tree.nodes.new("CompositorNodeGlare")
        glare.glare_type = "FOG_GLOW"
        glare.quality = "HIGH"
        glare.threshold = 0.9
        glare.size = 7
        comp = tree.nodes.new("CompositorNodeComposite")
        tree.links.new(rl.outputs["Image"], glare.inputs[0])
        tree.links.new(glare.outputs[0], comp.inputs[0])
        tree.links.new(rl.outputs["Alpha"], comp.inputs[1])


def apply_param_overrides():
    if not PARAMS_FILE:
        return
    import json

    with open(PARAMS_FILE, encoding="utf-8") as f:
        overrides = json.load(f)
    import vrm_anime_shader as vas

    for mat in bpy.data.materials:
        if not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "GROUP" and node.node_tree and node.node_tree.name == vas.SHADER_GROUP_NAME:
                for sock_name, value in overrides.items():
                    if sock_name in node.inputs:
                        try:
                            node.inputs[sock_name].default_value = value
                        except Exception:
                            pass


def main():
    rs.log("pose args", ARGS)
    rs.enable_addons()
    rs.clear_scene()
    model = rs.import_vrm(VRM)
    arm = model["arm"]
    model_other = None
    other_arm = None
    if MODE == "both":
        model_other = rs.import_vrm(VRM)
        other_arm = model_other["arm"]
        rs.set_model_visible(model_other, False)

    mn, mx = rs.bbox_of(model["meshes"])
    size = mx - mn
    center = (mn + mx) / 2

    # pose before conversion (geometry is the same either way)
    ops = POSES.get(POSE, POSES["idle"])
    apply_ops(arm, ops)
    if other_arm:
        apply_ops(other_arm, ops)
    bpy.context.view_layer.update()

    # recompute bounds after posing
    mn, mx = rs.bbox_of(model["meshes"])
    size = mx - mn
    center = (mn + mx) / 2
    rs.log("posed bbox", tuple(round(v, 3) for v in mn), tuple(round(v, 3) for v in mx))

    import vrm_anime_shader as vas

    def convert_one(a):
        bpy.context.view_layer.objects.active = a
        for o in bpy.context.selected_objects:
            o.select_set(False)
        a.select_set(True)
        return vas.convert_armature_materials(a, bpy.context, PRESET)

    converted, skipped = convert_one(arm)
    rs.log("converted", converted, "skipped", skipped)
    if other_arm:
        rs.log("other model kept as original MToon (not converted)")

    setup_showcase_world(LIGHT)
    setup_showcase_lights(LIGHT, center, size.z)
    setup_backdrop(center, LIGHT)
    setup_showcase_camera(center, size, YAW, head=rs.head_anchor(arm))
    configure_quality()
    apply_param_overrides()
    bpy.context.view_layer.update()

    base = os.path.join(OUT_DIR, TAG)
    os.makedirs(OUT_DIR, exist_ok=True)

    if MODE == "both" and model_other:
        rs.set_model_visible(model, False)
        rs.set_model_visible(model_other, True)
        bpy.context.view_layer.update()
        rs.render_to(base + "_orig.png")
        rs.set_model_visible(model_other, False)
        rs.set_model_visible(model, True)
        bpy.context.view_layer.update()
        rs.render_to(base + "_conv.png")
    else:
        rs.render_to(base + ".png")
    rs.log("DONE", base)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

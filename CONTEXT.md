# Domain Glossary — VRM Anime Shader

## Core Concepts

**MToon1**
: VRoid's cel-shaded material standard for VRM 1.0. Uses a complex node group (`Mtoon1Material.Mtoon1Output`) with 34+ input sockets covering lit/shade color, shading curve, rim, matcap, outline, emission, and UV animation.

**Anime Shader (VRM_AnimeShader)**
: Our custom Blender node group that replaces MToon1. Currently has 16 inputs: Base Color, Shadow Color/Threshold/Smoothness, Rim Color/Strength/Threshold, Specular Color/Strength/Smoothness, Shadow Tint Strength, Saturation, Brightness, Emission Strength, **Emission Color**.

**CompatShader / CompatibleShader**
: A Principled BSDF node kept alongside MToon1 in VRM materials for compatibility with non-VRM renderers. Receives the same Base Color texture and Normal map.

## Node Topology

**Triangle Topology**
: VRoid materials use three parallel processing paths: MToon1Output group (cel shading), CompatibleShader (Principled BSDF for fallback), and a Mix Shader that blends them. A "Unaffected Link To Active Output" shader bypasses all processing for non-VRM exporters.

**Shading Curve**
: The core cel-shading math inside MToon1Output. Uses ShaderToRGB → Map Range + Math nodes to apply Toony (hardness) and Shift (threshold) parameters to a Diffuse BSDF output.

**UV Processing Chain**
: Each texture goes through: UV Animation (rotation/translation over time) → UV Wrap (GL_REPEAT/CLAMP/MIRROR) → Texture Image node.

## Material Types

**Instance Material** (`N00_xxx (Instance)`)
: The main VRM material with full MToon1 processing. Contains all texture nodes.

**Outline Material** (`MToon Outline (N00_xxx)`)
: A separate material slot for the outline pass. Uses the same MToon1Output group with `Is Outline = True`.

## Known Issues

**INVALID (Purple) Shader** (FIXED)
: Caused by connecting a `(0,0,0)` default Normal vector to Diffuse BSDF's Normal input. Fixed by removing Normal socket from group entirely; unconnected Diffuse BSDF Normals use geometric normals correctly.

**Blender 4.4 Compatibility**
: `ShaderNodeOutputMaterial` has no "Normal" input. `NodeSocketVector` has no "NORMAL" subtype.

## Changelog

**2026-07-24 — v1.0.0 fixes**
- Removed broken Normal input socket from group (caused purple shader)
- Added `Emission Color` socket (default white) — emission textures now connect here instead of overwriting `Base Color`
- Moved `extract_mtoon_params()` before node cleanup so MToon group nodes still exist for parameter extraction
- Added missing UV connection for emissive texture nodes
- Fixed `KeyError: "Surface"` / `KeyError: "Normal"` by adding existence guards
- Fixed `TypeError: enum "NORMAL" not found` on `NodeSocketVector`
- **Ambient fill**: Added MixRGB(MULTIPLY×0.3) of Base Color + MixRGB(ADD) controlled by shadow ramp Fac, so ambient only boosts shadow areas (not lit areas)
- **Alpha handling**: Added `Alpha` input socket, Transparent BSDF, and Mix Shader at output for MASK/BLEND materials; Alpha output from base texture connected when alpha mode is MASK or BLEND
- **Image access safety**: Wrapped all `.image` accesses in try/except to prevent VRM addon blocking errors (`Cannot read "image.png"`)
- **Group inputs**: Added `Alpha` to `required_inputs` set for caching validation
- **Specular overexposure fix**: Changed `Spec Overlay` from OVERLAY→ADD mode; set `Spec Tint` Color1 default to black (was white); moved `Specular Strength` connection to `Spec Overlay.Fac` (was connected to `Spec Tint.Color1` causing all-white output → OVERLAY with white = pure white bleaching)
- **Diffuse BSDF uses pure white** (was connected to Base Color texture): so ShaderToRGB extracts pure lighting, not texture-tinted lighting. Fixes dark texture areas being forced into shadow zone.
- **Emission Strength uses MToon extracted value**: was hardcoded to 0.5 whenever an emissive texture existed, causing washout on face/skin materials. Now uses the MToon param (default 0.0).
- **Ambient fill reduced from 0.3→0.1**: less aggressive shadow boost to prevent washout.

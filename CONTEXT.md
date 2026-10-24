# Domain Glossary — VRM Anime Shader

## Core Concepts

**MToon1**
: VRoid's cel-shaded material standard for VRM 1.0. Uses a complex node group
(`Mtoon1Material.Mtoon1Output`) with 34+ input sockets covering lit/shade color,
shading curve, rim, matcap, outline, emission, and UV animation. VRM 0.0 files are
imported by the VRM add-on through a MToon0 → MToon1 migration, so the same
`material.vrm_addon_extension.mtoon1` API is available after import.

**Anime Shader (VRM_AnimeShader)**
: Our custom Blender node group that replaces MToon1. v2 has 26 inputs:
Base Color, Shade Color, Shade Texture, Shade Shift, Shade Toony, Shift Influence,
Shadow Color/Threshold/Smoothness, Shade Tint Strength, Light Normalize,
Ambient Floor, Light Response, Light Tint, Rim Color/Strength/Threshold,
Specular Color/Strength/Smoothness, Saturation, Brightness, Emission Color/Strength,
Alpha, Normal → Surface.

**Scene-light driven toon shader**
: The core idea of v2: sample the real EEVEE irradiance through a white Diffuse BSDF
and `ShaderToRGB`, compress it into a 0..1 light level, and use that both for the
two-tone terminator and for exposure/colour integration.

**Light Normalize (k)**
: Compression constant for `x = luma / (luma + k)`. Lets a single Threshold work in
dim and bright scenes. Lower k = more sensitive to dim light.

**Ambient Floor / Light Response**
: Final exposure follows scene brightness: `exposure = 1 + (min(1.25, Ambient Floor +
x·1.35) − 1) · Light Response`. `Light Response = 0` is scene-independent (faithful);
higher values make the character darken in dark scenes and brighten outdoors.

**Light Tint**
: How strongly the normalised chroma of the scene light tints the character.
0 = neutral, 1 = fully coloured by scene light (strong sunset/neon tint).

**MToon Shift / Shade Shift / Shade Toony**
: Per-material values taken from MToon. The shader computes
`effective threshold = Shadow Threshold − Shade Shift × Shift Influence`, and the
terminator softness is scaled by `(1 − 0.8 · Shade Toony)`. `Shift Influence = 1`
honours MToon exactly (a shift≈1 model stays fully lit); lower values let the preset
add stylised shading on top of the authored look.

**Albedo gate**
: Additive specular/rim is multiplied by `max(min(base_luma·1.8, 1), 0.06)` so black
cloth does not receive a grey sheen.

**MToon Faithful**
: Preset with `Light Response = 0`, `Light Tint = 0`, `Shift Influence = 1`, no
rim/specular. It reproduces the original MToon group pixel-for-pixel and is used as
the regression baseline.

## Node Topology

**Triangle Topology**
: VRoid MToon materials use three parallel processing paths: MToon1Output group
(cel shading), CompatibleShader (Principled BSDF for fallback), and a Mix Shader
that blends them. Conversion keeps only the texture nodes and rebuilds the tree
around `VRM_AnimeShader` + Material Output.

**Light Probe**
: `Diffuse BSDF(white, geometric normal)` → `ShaderToRGB` → dot with luminance
weights → `luma`. Used for the toon factor, light chroma and exposure. Geometric
(non-normal-mapped) normal is deliberate: painted face/hair normals otherwise create
noisy toon patches.

**Toon Factor**
: `x = luma / (luma + Light Normalize)`, then a clamped Map Range from
`threshold − smooth` to `threshold + smooth`. 0 = shade, 1 = lit.

**Light Chroma**
: `LightToRGB.Color / luma`, mixed from white by `Light Tint`, multiplied into the
lit/shade colour. This is what makes the character accept coloured scene lights.

**Shade Chain**
: `Shade Color × Shade Texture` → multiplied by `mix(white, Shadow Color, Tint Strength)`
→ mixed with Base Color by the toon factor.

**Specular Chain**
: `Glossy BSDF(roughness = 1 − Specular Smoothness, normal-mapped)` → `ShaderToRGB` →
luma → Map Range mask → × Specular Color × light chroma × albedo gate × strength.

**Rim Chain**
: `Fresnel` (geometric normal) → Map Range mask → × Rim Color × light chroma × albedo gate
× strength.

**Alpha**
: MASK materials use `base alpha × baseColorFactor.alpha > alpha cutoff` as a hard
cut with the `DITHERED` render method; BLEND materials keep alpha and use `BLENDED`.

## Material Types

**Instance Material** (`N00_xxx (Instance)`)
: The main VRM material with full MToon1 processing. Contains all texture nodes.

**Outline Material** (`MToon Outline (N00_xxx)`)
: Separate materials used by the VRM add-on's MToon outline **geometry node** modifiers.
They are not part of the mesh material slots and are intentionally not converted;
conversion skips anything whose name contains `MToon Outline`.

**Role-named texture nodes**
: The VRM importer names texture nodes `Mtoon1<Role>Texture.Image`, e.g.
`Mtoon1BaseColorTexture.Image`, `Mtoon1ShadeMultiplyTexture.Image`,
`Mtoon1NormalTexture.Image`, `Mtoon1EmissiveTexture.Image`,
`Mtoon1MatcapTexture.Image`, `Mtoon1ShadingShiftTexture.Image`. Conversion uses these
roles, not heuristics.

## Known Issues

**INVALID (Purple) Shader** (FIXED)
: Caused by connecting a `(0,0,0)` default Normal vector to a BSDF's Normal input.
Fixed by always feeding the group Normal socket from a Normal Map node (with a flat
default normal when there is no normal texture).

**Blender 4.4 Compatibility**
: `ShaderNodeOutputMaterial` has no "Normal" input. `NodeSocketVector` has no "NORMAL"
subtype. `ShaderToRGB` is EEVEE-only.

**Group version upgrades**
: The group carries a `vas_version` custom property. If the interface/version changes,
`ensure_anime_shader_group` rebuilds the group, but already-converted materials then
reference a stale group. Re-import and convert again after upgrading the addon.

## Changelog

**2026-10-24 — v2.0.0 (scene-light pipeline)**
- Rebuilt `VRM_AnimeShader` group from scratch (version tag `vas_version = 3`).
- Replaced the flat "unlit albedo + fake rim/spec" pipeline with a scene-light driven
  toon pipeline: white Diffuse probe → `ShaderToRGB` → compressed light level `x`.
- Per-material MToon data is now used: shade colour factor, shade multiply texture,
  shading shift/toony, normal map, emissive factor × texture × KHR strength.
- Light colour tint and exposure response make the character accept coloured lights,
  HDRI/world light and dark/bright environments.
- Real Glossy-BSDF specular sampled from scene lights (instead of the old
  Diffuse+Glossy mix ramp), with an albedo gate so black cloth no longer turns grey.
- Rim uses geometric Fresnel + light tint, also albedo-gated.
- MASK alpha uses a hard `> cutoff` cut instead of relying on dithering.
- Base colour factor and double-sided/backface culling are applied per material.
- Added `MToon Faithful` preset (pixel-identical to original MToon) and `Shift
  Influence` control; presets now expose Light Normalize/Response/Tint and Ambient Floor.
- Removed per-material shadow colour extraction; shadows come from
  `Shade Color × Shade Texture` plus optional global tint.
- Blender 4.4.3 validated on VRM 0.0 and VRM 1.0 models; faithful mean abs pixel
  difference ≈ 0.02/255.

**2026-10-24 — v2.0.2 (hotfix)**
- Fixed `AttributeError: 'VAS_OT_convert_mtoon' object has no attribute 'enabled'`
  raised while drawing the "VRM Anime Shader" sidebar panel: operator buttons must
  disable the layout `row`, not the operator properties.
- Avoid re-syncing Scene shader properties to every material on every panel redraw
  (cache the inspected material); this removes UI redraw lag on larger models.

**2026-10-24 — v2.0.1 (showcase tooling)**
- Added `dev/showcase/`: headless comparison harness (`render_scene.py`), pose
  showcase renderer (`pose_showcase.py`), compositing helpers and a per-shot shader
  override example (`params_neon.json`).
- Added posed showcase previews under `docs/showcase/` and linked them from the README.
- No shader/conversion behaviour changes in this commit.

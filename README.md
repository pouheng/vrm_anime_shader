# VRM Anime Shader

Converts VRM MToon 1.0 materials to a custom anime-style node group for Blender EEVEE.

## Installation

1. Clone or copy this folder to `Blender/4.4/scripts/addons/vrm_anime_shader/`
2. Enable in Blender Preferences → Add-ons → search "VRM Anime Shader"
3. Import a VRM model (requires VRM addon), select its armature, open `Sidebar → Anime Shader`

## Usage

1. Select the VRM armature → click **Convert All Materials**
2. All MToon materials are replaced by the `VRM_AnimeShader` group
3. Adjust **Shader Parameters** in the panel — changes sync to every material in real time
4. Switch between built-in presets: *Anime Clean*, *Wuthering Waves*, *Genshin Impact*, *Honkai Star Rail*, *Flat Cel Shade*, *Soft Anime*

### Parameters

| Section | Controls |
|---------|----------|
| Shadow | Color, Threshold (lit/shadow cutoff), Smoothness, Tint Strength |
| Rim Light | Color, Strength, Threshold |
| Specular | Color, Strength, Smoothness |
| Color Adjust | Saturation, Brightness |
| Emission | Strength |

## Architecture

### Processing Chain

```
Base Color → Diffuse BSDF → ShaderToRGB → Math(ADD +0.25) → ColorRamp(LINEAR)
                                                                     │
                                          ┌──────────────────────────┘
                                          ↓
            Shadow Tint (Base × Shadow Color) ← mix(Fac=ramp) → HSV → MixRGB(ADD, Emission)
                                                                       │
Rim: Fresnel → ColorRamp → Mix(Rim Color) → MixRGB(ADD, Fac=Rim Strength)
                                                                       │
Spec: Diffuse+Glossy → ShaderToRGB → ColorRamp → Tint → MixRGB(ADD, Fac=Spec Strength)
                                                                       │
                                                                       ↓
                                                           Final Emission → MixShader(Fac=Alpha) → Output
                                                                          /
                                                             Transparent BSDF
```

Key design choices:

- **Base Color → Diffuse BSDF**: The texture modulates the lighting luminance, so dark texture areas naturally sit closer to the shadow zone — authentic cel-shading behavior
- **Math(ADD +0.25) before ramp**: Ensures the texture stays visible even in scenes with no direct lighting (Render mode without lights)
- **LINEAR ramp**: White at 0.0 (full shadow), black at threshold (full lit). Smooth gradient avoids hard banding
- **Per-material Shadow Color removed**: MToon's extracted `shade_color` values are very bright (~0.93–1.0), causing a flat look. All materials use a uniform dark default
- **Scene-level properties**: One UI panel syncs to all materials via `_sync_param_to_all()`. No per-material overrides
- **Specular uses ADD mode** (not OVERLAY) with Fac driven by the strength slider — prevents bleaching

### Texture Tracing

The addon traces MToon group input connections backward through the UV animation chain to find texture nodes. It does **not** rely on node names (which contain unstable Unicode). Every `.image` access is wrapped in `try/except` because the VRM addon blocks direct reads.

## Technical Notes

### Blender 4.4 Compatibility

| Issue | Workaround |
|-------|-----------|
| `ShaderNodeOutputMaterial` has no Normal input | Pass normals through BSDF nodes |
| `NodeSocketVector` lacks NORMAL subtype | Leave Normal disconnected → geometric normals |
| `LIGHT_FILTER` icon missing | Use `LIGHT_DATA` |
| Default Normal `(0,0,0)` on BSDF = purple | Never connect a zero Normal vector |

### Limitations

- **Outline materials** (`MToon Outline (xxx)`) are skipped during conversion
- **Shade/MatCap/Rim textures** from MToon are not carried over (only the base and emissive textures are preserved)
- **Material Preview** may appear overexposed under Blender's default studio lighting — adjust Rim/Specular Strength down, or rely on final Render mode
- **Normal maps** are disconnected (caused invalid shader in earlier versions)

## License

MIT

# Headless showcase / comparison harness

These scripts render the comparison and posed showcase images used in the main
README. They run fully headless (`blender -b`) and assume:

- Blender 4.4.x (tested on 4.4.3) with the VRM add-on installed as the
  `bl_ext.user_default.vrm` extension.
- This add-on installed in `Blender/4.4/scripts/addons/vrm_anime_shader/`.
- A VRM model with a MToon 1.0 / MToon 0.0 material set.

The scripts enable the add-ons themselves, so `--factory-startup` is fine.

## Posed showcase renders

```bash
blender -b --factory-startup --python pose_showcase.py -- \
    --vrm "model.vrm" \
    --out out/showcase_pose \
    --pose wave \            # idle | wave | point | lookback
    --light outdoor \        # studio | outdoor | sunset | night | color
    --preset wuthering_waves \
    --res 1080x1500 --samples 64 \
    --frame full \           # full | upper | portrait
    --yaw 22 \
    --tag wave-outdoor-wuthering
```

Use `--mode both` to render the original MToon and the converted character from the
same pose/camera/lighting (outputs `_orig.png` and `_conv.png`).

`--params params_neon.json` applies per-shot shader overrides on top of the preset
(any group input socket name is accepted).

Poses are defined in the `POSES` dict at the top of `pose_showcase.py`; each entry is a
list of `("aim", bone, direction)` / `("rot", bone, axis, degrees)` operations in
armature space.

## Comparison / lighting sweep renders

```bash
blender -b --factory-startup --python render_scene.py -- \
    --vrm "model.vrm" --out out/final --tag studio-clean \
    --view face --light studio --preset anime_clean \
    --res 1200x800 --samples 32
```

`--view full|upper|face`, `--light studio|outdoor|sunset|sky|night|color|world`,
and `--no-outline` / `--ground` switches are supported. Use `--convert-addon
path\to\old\addon.py` to swap in another converter version and produce a
before/after baseline.

## Compositing

- `compose.py` — side-by-side labelled comparison from two renders.
- `compose_showcase_final.py` — 3×2 pose showcase sheet with captions.

Both use Pillow (`pip install pillow`) and expect the images produced above.

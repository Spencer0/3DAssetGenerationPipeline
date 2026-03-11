# Blender Script Usage

## Templates
- Tree: `blender --background --python blender/scripts/template_tree.py`
- Fence: `blender --background --python blender/scripts/template_fence.py`
- Apartment: `blender --background --python blender/scripts/template_apartment.py`
- Car: `blender --background --python blender/scripts/template_car.py`

## Props
- Fruit: `blender --background --python blender/scripts/prop_fruit.py`
- Basketball: `blender --background --python blender/scripts/prop_basketball.py`
- Vending: `blender --background --python blender/scripts/prop_vending_machine.py`

## Export
- `blender --background --python blender/scripts/export_glb.py -- --out threejs-test/assets/preview.glb`

## Palette Library
- Build and save a shared material library:
  - `blender --background --python blender/scripts/build_palette_library.py -- --out blender/palette_library.blend`

## Validation
- `blender --background --python blender/scripts/validate_asset.py -- --asset_type tree`

## Parameters (examples)
- Tree: `--trunk_height 2.5 --canopy_radius 1.6`
- Fence: `--length 4 --post_spacing 0.6`
- Apartment: `--width 10 --depth 14 --height 16`
- Car: `--length 4.2 --width 1.7 --height 1.5`

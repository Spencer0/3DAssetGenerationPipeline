# Blender Script Usage

## Templates
- Tree: `blender --background --python blender/scripts/template_tree.py`
- Fence: `blender --background --python blender/scripts/template_fence.py`
- Apartment: `blender --background --python blender/scripts/template_apartment.py`
- House (1 floor): `blender --background --python blender/scripts/template_house.py -- --floors 1 --out threejs-test/assets/house_1f.glb`
- House (2 floor): `blender --background --python blender/scripts/template_house.py -- --floors 2 --out threejs-test/assets/house_2f.glb`
- Car base (sedan): `blender --background --python blender/scripts/build_sedan_base.py`
- Car base (truck): `blender --background --python blender/scripts/build_truck_base.py`

## Props
- Fruit: `blender --background --python blender/scripts/prop_fruit.py`
- Basketball: `blender --background --python blender/scripts/prop_basketball.py`
- Vending: `blender --background --python blender/scripts/prop_vending_machine.py`
- Traffic sign (stop): `blender --background --python blender/scripts/prop_traffic_sign.py -- --variant stop --out threejs-test/assets/traffic_sign_stop.glb`
- Traffic sign (triangle): `blender --background --python blender/scripts/prop_traffic_sign.py -- --variant triangle --out threejs-test/assets/traffic_sign_triangle.glb`
- Traffic sign (square): `blender --background --python blender/scripts/prop_traffic_sign.py -- --variant square --out threejs-test/assets/traffic_sign_square.glb`

## Export
- `blender --background --python blender/scripts/export_glb.py -- --out threejs-test/assets/preview.glb`

## Car Variants
- Sedan variant: `blender --background --python blender/scripts/export_sedan_variant.py -- --out threejs-test/assets/car_sedan.glb`
- Truck color: `blender --background --python blender/scripts/export_truck_color.py -- --out threejs-test/assets/car_truck.glb`

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

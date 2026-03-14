# Katamari Asset Generator

This repo is a starter pipeline for a retro-anime, medium-poly asset kit exported as `.glb` and previewed in Three.js.

## What you get
- A **style guide** for consistent scale, materials, and colors.
- **Blender Python scripts** for templated assets (tree, fence, apartment, car) and simple props (fruit, basketball, vending machine).
- A minimal **Three.js test viewer** to validate scale, pivots, and materials.

## Quick start
1. Open Blender and save a new `.blend` in this repo.
2. Run a script:
   - `blender --background --python blender/scripts/template_tree.py`
3. Export:
   - `blender --background --python blender/scripts/export_glb.py -- --out threejs-test/assets/tree.glb`
4. Preview:
   - `npm install`
   - `npm run dev`
   - Open the URL printed by Vite.

## Notes
- Scripts assume **Blender 3.6+** and use **meters** as the unit.
- Geometry Nodes are created programmatically for template assets.
- All exports target **glTF 2.0 / GLB** with PBR materials.

## Project layout
- `docs/style-guide.md`: Palette, materials, proportions, and naming rules.
- `docs/asset-specs.md`: Target sizes and pivots for each asset.
- `docs/export-checklist.md`: GLB export rules and Three.js validation steps.
- `docs/prefabs.md`: Prefab chunk format and export notes.
- `blender/scripts/`: Asset generation + export scripts.
- `threejs-test/`: Minimal viewer to check assets.
- `threejs-test/tools/`: Manifest generator for batch preview.

# Retro-Anime Style Guide

## Scale and Units
- Blender units: **meters**.
- Three.js convention: **1 unit = 1 meter**.
- Apply transforms before export.

## Shape Language
- Medium-poly, simplified silhouettes.
- Visible bevels on hard edges (small, consistent radius).
- Exaggerated proportions over realism.

## Materials (PBR)
- BaseColor + Roughness + Metalness (matte by default).
- Default targets:
  - Roughness: 0.7 to 0.9
  - Metalness: 0.0 (unless explicitly metal)
- Avoid noisy normal maps early; use geometry for shape.

## Palette (primary)
- Cream: #F4E7C5
- Sakura: #F3A6B8
- Sky: #7FB5E6
- Mint: #8ED3B5
- Charcoal: #2E2E33
- Asphalt: #5B5B63
- Lemon: #F2D45C
- Accent Red: #E85C4A

## Naming
- Meshes: `assetName_part` (e.g. `tree_trunk`)
- Materials: `MAT_assetName_variant`
- Collections: `asset_<name>`

## Pivots
- Props: bottom center.
- Modular: grid-aligned corner or center (document in asset spec).

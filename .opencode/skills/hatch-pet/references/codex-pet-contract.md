# OpenPets Runtime Contract (V1 Project Scope)

Baseline: OpenPets v4.1.0, commit `963ad049fe08c465c822ee5cc7ff02e93f28b232`. Historical Codex authoring conventions are not the runtime package contract.

## Supported Output

- V1 base package root: exactly `pet.json` and `spritesheet.webp`, no enclosing directory, symlinks, additional files or directories.
- Atlas: one fully decodable transparent WebP, `1536x1872`, 8 columns × 9 rows, `192x208` cells and 57 used frames. Unused cells transparent; project QA also clears transparent RGB residue.
- Keep full-resolution detail. A 2x pixel grid is optional, not required by the host.
- PNG is an intermediate/reference format, not the manifest-selected runtime atlas in this project.

## Metadata

```json
{
  "id": "pet-name",
  "displayName": "Pet Name",
  "description": "One short sentence.",
  "spritesheetPath": "spritesheet.webp"
}
```

ID matches `^[a-z0-9][a-z0-9_-]{0,63}$` and cannot be `builtin`. Name and description must be non-empty and at most 80/500 UTF-16 code units. Bounds: metadata 128 KiB, atlas 100 MiB, ZIP 50 MiB. Installed folder ID matches metadata; local source folders may have a different name. Use manual OpenPets ZIP/folder import, not a required `${CODEX_HOME}` path.

For V1, omit `spriteVersionNumber` entirely: a supplied marker can only be 2 in OpenPets. This packager rejects any version marker and wardrobe metadata to avoid claiming unsupported output. Optional catalog fields such as category/subcategory/sourceUrl are kept in the published manifest.

## Host-Owned Behavior

The host selects row, equal-time cycle duration, reaction mapping and movement. See `animation-rows.md`. Asset changes cannot configure arbitrary per-frame FPS. State changes can occur mid-cycle without a separate transition row. User reduced-motion settings may disable playback.

## Optional New Formats, Not Implemented Here

- V2: 8×11, `1536x2288`, `spriteVersionNumber: 2`; the original nine actions plus row0/column6 neutral pose and 16 static gaze directions in rows9–10. Not extra agent action states. Optional normalized `gazeAnchor` requires V2 artwork for gaze behavior.
- Static SVG: exact atlas dimensions and strict vector whitelist. No scripts, CSS, external references or embedded raster. Do not wrap this project's PNGs in SVG to claim support.
- Wardrobe: additional full atlases under `outfits/` with manifest-declared outfits and optional schedules. V1 may have outfits; an outfit-free base ZIP still uses two files. Adding outfits does not require replacing the base artwork, but requires new assets and package validation together.

Sources at the fixed commit: `apps/desktop/src/codex-pets-core.ts`, `pet-installation.ts`, `pet-file-safety.ts`, `pet-wardrobe-core.ts`, `packages/install-pet/src/spritesheet.ts`, `docs/pets.md` in https://github.com/OpenPetsHQ/openpets.

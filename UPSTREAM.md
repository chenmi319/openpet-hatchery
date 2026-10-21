# Upstream

The project skills are derived from `openai/skills` at commit:

```text
49f948faa9258a0c61caceaf225e179651397431
```

Vendored paths:

- `skills/.curated/hatch-pet`
- `skills/.system/imagegen`

Both upstream directories are Apache-2.0 licensed. Their `LICENSE.txt` files remain beside the derived skills.

OpenCode adaptations:

- Replaced Codex runtime paths, built-in image tooling, and worker delegation with project-local OpenCode skill instructions and serial CLI calls.
- Required ignored local proxy configuration with a separate key file; disabled environment/default endpoint fallback and batch generation.
- Added request-attempt ledger statistics and URL-response download validation; removed the historical cumulative budget cap while retaining serial approval gates and disabling SDK automatic retries.
- Added pet-specific animation action overrides.
- Added optional strict 2x pixel-grid composition and validation; current default preserves full 192x208 detail with scale 1.
- Changed package paths to this repository's `work/`, `previews/`, and `dist/` layout.
- Removed Codex-only CLI/network references that contradict this project's fail-closed runtime contract.
- Added whole-pet review before targeted repairs, consolidated feedback and delegated stage delivery; clarified perceptual geometry checks, masked-reference ordering and local result recovery without changing the image adapter or accepted assets.

Runtime contract sync baseline: OpenPets v4.1.0 at `963ad049fe08c465c822ee5cc7ff02e93f28b232` in https://github.com/OpenPetsHQ/openpets. This is separate from the pinned source of the vendored authoring tools above; tools were not replaced wholesale. Synced host equal-time previews, metadata/package bounds and persona-action rules. Kept V1 WebP base output; did not add V2 gaze, SVG or wardrobe output and did not replace accepted pet assets.

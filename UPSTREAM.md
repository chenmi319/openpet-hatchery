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
- Added paid-call ledger enforcement and URL-response download validation.
- Added pet-specific animation action overrides.
- Added strict 2x pixel-grid composition and validation.
- Changed package paths to this repository's `work/`, `previews/`, and `dist/` layout.
- Removed Codex-only CLI/network references that contradict this project's fail-closed runtime contract.

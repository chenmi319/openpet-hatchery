# OpenPet Hatchery

A reproducible toolkit, OpenCode skills, and multi-pet management framework for creating, validating, and packaging community OpenPets companions and multi-kit wardrobes.

## Quickstart: Hatchery CLI

The hatchery provides a unified CLI (`scripts/hatchery.py`) for managing the full lifecycle of any number of pets:

```bash
# 1. List all managed pets, wardrobe outfits, and package statuses
python scripts/hatchery.py list

# 2. Scaffold a brand-new pet from standardized templates
python scripts/hatchery.py new cyber-cat --name "Cyber Cat" --category "western"

# 3. Register a new wardrobe outfit for an existing pet
python scripts/hatchery.py add-outfit cyber-cat neon-suit --name "Neon Suit"

# 4. Validate pixel residue, grid alignments, and wardrobe integrity
python scripts/hatchery.py validate [pet-id]

# 5. Compile and package production-ready release ZIPs
python scripts/hatchery.py package [pet-id]
```

## Reference Pet: GOAT Leo

The flagship reference pet implemented in this repository is **GOAT Leo**, an unofficial fan-made pixel companion featuring a 2-outfit wardrobe (114 animated frames total):

This project is not affiliated with or endorsed by Lionel Messi, any federation, any club, or OpenPets.

```bash
# Install via OpenPets CLI:
npx -y install-pet goat-leo
```

The official release package is also available from [OpenPets Gallery](https://openpets.dev/pets/goat-leo-openpets).

## Repository Architecture

```text
.opencode/skills/       OpenCode hatch-pet and imagegen skill workflows
config/                 Public, non-secret generation defaults
pets/
  _template/            Standardized scaffolding templates (spec.md, identity.txt, state-overrides.json)
  <pet-id>/             Per-pet identity, action overrides, and authoring specifications
previews/<pet-id>/      Final thumbnail, contact sheet, and GIF previews
dist/
  <pet-id>/             Runtime files (pet.json, spritesheet.webp, outfits/*.webp)
  <pet-id>.zip          Gallery-ready, single-file release package
submissions/            Gallery submission copy
scripts/
  hatchery.py           Unified multi-pet lifecycle and wardrobe management CLI
  package_pet.py        Official OpenPets pet validator and packager
work/<pet-id>/          Local candidates, prompts, frame extractions, ledgers, and QA
```

## Setup

```bash
uv sync
```

`uv sync` installs the locked project dependencies and the `dev` group (Ruff and Pyright) into `.venv`; no global tool installation is required. `pyrightconfig.json` points type checking at this environment.

Live image generation uses a local ignored file. Create it from the example:

```bash
cp .imagegen.local.example.json .imagegen.local.json
```

Set its private `baseUrl` and `apiKeyFile` path. The key remains in the separate secret file. The adapter fails closed when the local config or either field is absent; it never reads proxy settings from the OpenCode environment and never falls back to the official OpenAI endpoint.

Restart OpenCode after cloning or changing files under `.opencode/skills/`, then ask it to use `hatch-pet` for a pet specification under `pets/`.

## Review and Repair Workflow

For an existing pet, deliver a whole review candidate first: all nine actions, normal-speed and diagnostic slow animations, one same-scale preview page, and per-row sources and known defects. Ask for one consolidated usable / needs repair / change design review, then repair the prioritized action rather than repeatedly asking about single frames.

Within an explicitly approved stage, the agent may make delegated visual decisions and perform serial, targeted edits. Each stage delivers a complete action and before/after comparison; request errors stop the stage, and repeated edits without visible progress require a different approach. Counts are statistics, not permission for retries or unrelated work. "No visible size changes or drift" does not imply an unapproved zero-pixel-difference requirement; masks and format checks do not prove visual correctness.

Review candidates and optional ZIPs stay under `work/`, clearly labeled as provisional. Existing final assets remain unchanged until visual acceptance and promotion authorization; a same-ID manual import may replace the installed pet. No hand-painted anatomy, mirrored numbers, duplicated frames or timing tricks are used to conceal missing animation.

See [the detailed review workflow](.opencode/skills/hatch-pet/references/review-workflow.md) for stage boundaries, grounded image references, result recovery and verification scope. This workflow update does not regenerate or promote any pet assets.

## Validation

No-cost checks:

```bash
uv run --locked ruff check .opencode scripts tests
uv run --locked pyright
uv run python -m compileall -q .opencode scripts tests
uv run python -m unittest discover -s tests -v
uv run python .opencode/skills/imagegen/scripts/image_gen.py generate \
  --prompt "dry run" \
  --dry-run \
  --out work/dry-run.png
```

Final packages are imported manually into OpenPets before any Git or Gallery publication.

## Runtime Compatibility and Authoring Boundaries

The current pipeline targets **OpenPets v4.1.0 V1 WebP pets**: 8×9 cells, 192×208 per cell, 57 used frames. V1 remains supported and natively supports wardrobes without V2 gaze or SVG. See `.opencode/skills/hatch-pet/references/codex-pet-contract.md` for metadata and file limits.

Previews use the host's equal-time cycle baseline, including 5500ms Idle and Normal/Relaxed waiting (1010/2200ms). GIF rounding is distributed at 10ms precision; previews loop for review while host waving/success/failure default to two cycles. Existing checked-in preview GIFs are historical and have not been regenerated during the contract sync; regenerate from accepted frames when reviewing a new candidate. A preview is not an actual host import test.

Live image requests remain serial, approval-gated and recorded before sending. The ledger counts attempts without a cumulative cap; failures still count because billing may have occurred. Legacy `--max-calls`/`maxCalls` warn and are ignored. SDK automatic retries remain disabled. Counts do not authorize more calls.

The installed `@open-pets/opencode@4.1.0` plugin emits six automatic reactions using five distinct default atlas rows; host Idle makes six main animations. Its event triggers are described in `animation-rows.md`; ordinary read/search/non-test shell tools do not automatically select work. Desktop motion and waving are separate uses of the remaining rows.

Current GOAT Leo assets and their specifications remain the accepted historical version. Proposed dribbling-run and running-celebration designs need visual approval before replacing the package or its action descriptions. Updating the authoring rules does not mean those new animations are complete.

### Wardrobe Support

Wardrobes are supported on V1 WebP pets without converting to V2 or modifying the accepted base outfit. Each added outfit provides a full 8×9 atlas (1536×1872 WebP) under `outfits/{id}.webp` with identical layout, matching proportions, locked hair/face geometry, and approved actions.

`GOAT Leo` packages four complete outfits in a single release package `dist/goat-leo.zip`. The default and gold-number variant stay adjacent for easy comparison, followed by the classic red-blue and modern pink-black kits:
1. **Default Outfit (Classic Sky and White)**: Classic sky-blue and white vertical stripes with black #10 (`spritesheet.webp`). It is the golden reference for every action.
2. **Golden Farewell (`golden-farewell`)**: The default sky-blue and white kit with only the #10 recolored gold (`outfits/golden-farewell.webp`); stripes, shorts and every frame otherwise match the default outfit. Rebuild with `python pets/goat-leo/recolor/recolor.py golden-farewell && python pets/goat-leo/recolor/build_atlas.py golden-farewell`.
3. **Red and Blue Legend (`red-blue-legend`)**: Garnet and navy vertical stripes with golden-yellow #10 (`outfits/red-blue-legend.webp`). All nine rows are the default outfit's frames with only the kit recolored, so pose, face, hands, gaze, timing and placement match the default outfit pixel for pixel. Rebuild with `python pets/goat-leo/recolor/recolor.py && python pets/goat-leo/recolor/build_atlas.py`.
4. **Flamingo Pink (`flamingo-pink`)**: An approved Miami-inspired pink-and-black concept kit (`outfits/flamingo-pink.webp`), not a replica of a specific season's official uniform. The shirt and socks are pink, with near-black #10 and shorts; all nine rows preserve the default outfit's poses and source shading, including faint stripe-seam texture. Rebuild with `python pets/goat-leo/recolor/recolor.py flamingo-pink && python pets/goat-leo/recolor/build_atlas.py flamingo-pink`.

All recolored outfits share the same number mask. Short, arm-occluded strokes remain included; the right-running third frame uses a source-pixel-hash-bound mask because its number touches the sleeve outline. Replacing that base frame requires reviewing the mask again; the regression test rejects an outdated source hash.

The packager (`scripts/package_pet.py`) validates both the base atlas and all declared outfit atlases, ensuring complete directory integrity and packaging them into the single `dist/goat-leo.zip` install package. Users can switch between outfits via the OpenPets desktop context menu (**Outfit**).

The four-outfit package received user visual acceptance and a successful manual desktop import on 2026-10-22. Automated validation passed for all four atlases, with 28 tests passing; this records the reviewed package rather than a guarantee for other host versions.

## Licensing

Code and vendored skill derivatives use Apache-2.0; see `LICENSE` and `UPSTREAM.md`. Generated pet assets have separate terms in `ASSET-LICENSE.md`.
## Image model compatibility experiment

The image adapter additionally accepts `--model "Nano Banana 2.1" --quality auto` through the configured OpenAI-compatible endpoint for explicitly approved experiments. Its conservative compatibility profile rejects mask, background, output-format, output-compression, input-fidelity and moderation; it does not describe the capabilities of every provider. Prompts are limited to 4000 characters and references to 14. The server chooses the file format; check decoded format and transparency before treating the result as a pet asset. Provider settings remain in the ignored local configuration, with no provider-specific address or routing in the adapter. GPT defaults and the current formal assets are unchanged.

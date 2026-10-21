# OpenPet Hatchery

Project-local OpenCode skills, reproducible specifications, QA evidence, and final packages for community OpenPets pets.

The first pet is **GOAT Leo**, an unofficial fan-made pixel companion inspired by Lionel Messi's 2022 world-champion era. This project is not affiliated with or endorsed by Lionel Messi, any federation, any club, or OpenPets.

## Featured Pet

**GOAT Leo** is featured in the official [OpenPets Gallery](https://openpets.dev/pets/goat-leo-openpets).

```bash
npx -y install-pet goat-leo
```

The official package is available from [OpenPets](https://zip.openpets.dev/pets/goat-leo-openpets/goat-leo.zip).

## Layout

```text
.opencode/skills/       OpenCode hatch-pet and imagegen skills
config/                 Public, non-secret generation defaults
pets/<pet-id>/          Stable identity and animation specifications
previews/<pet-id>/      Final thumbnail, contact sheet, and GIF previews
dist/<pet-id>/          Final OpenPets runtime files
dist/<pet-id>.zip       Gallery-ready package
submissions/            Gallery submission copy
work/                   Ignored candidates, prompts, frames, ledgers, and QA work
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

`GOAT Leo` packages two complete outfits in a single release package `dist/goat-leo.zip`:
1. **Default Outfit**: Classic Argentina blue-and-white stripes (`spritesheet.webp`).
2. **Red and Blue Legend (`red-blue-legend`)**: Classic deep garnet and navy vertical stripes with golden-yellow #10 (`outfits/red-blue-legend.webp`).

The packager (`scripts/package_pet.py`) validates both the base atlas and all declared outfit atlases, ensuring complete directory integrity and packaging them into the single `dist/goat-leo.zip` install package. Users can switch between outfits via the OpenPets desktop context menu (**Outfit**).

## Licensing

Code and vendored skill derivatives use Apache-2.0; see `LICENSE` and `UPSTREAM.md`. Generated pet assets have separate terms in `ASSET-LICENSE.md`.
## Image model compatibility experiment

The image adapter additionally accepts `--model "Nano Banana 2.1" --quality auto` through the configured OpenAI-compatible endpoint for explicitly approved experiments. Its conservative compatibility profile rejects mask, background, output-format, output-compression, input-fidelity and moderation; it does not describe the capabilities of every provider. Prompts are limited to 4000 characters and references to 14. The server chooses the file format; check decoded format and transparency before treating the result as a pet asset. Provider settings remain in the ignored local configuration, with no provider-specific address or routing in the adapter. GPT defaults and the current formal assets are unchanged.

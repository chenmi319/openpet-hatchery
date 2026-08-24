---
name: hatch-pet
description: Create, repair, validate, preview, and package OpenPets V1 animated pets. Use when hatching a pet, building an 8x9 spritesheet, generating pet animation rows, or preparing an OpenPets Gallery package in this repository.
license: Apache-2.0
compatibility: OpenCode project skill; requires Python 3.11+, uv, Pillow, and the sibling imagegen skill.
metadata:
  upstream: openai/skills@49f948faa9258a0c61caceaf225e179651397431
---

# Hatch Pet

Create one OpenPets V1 pet from a checked-in specification. This repository may hold many pets, but each run handles exactly one pet.

## Required Inputs

Before work, read:

- `pets/<pet-id>/spec.md`
- `pets/<pet-id>/state-overrides.json`
- sibling skill `.opencode/skills/imagegen/SKILL.md`

Do not infer unresolved product choices. Do not use third-party reference photos unless the pet spec explicitly allows them.

## Hard Boundaries

- Use the sibling `imagegen` CLI for all generated visuals.
- Run every paid call serially. Never use subagents or `generate-batch`.
- Respect the call ledger and the 100-call hard cap. Never retry silently.
- Stop at every approval gate. User approval is required before downstream calls.
- Keep generated intermediates under `work/<pet-id>/`; never place secrets, API responses, signed URLs, or failed candidates in tracked output.
- Do not initialize Git, commit, push, create a repository, or submit to Gallery.
- Do not mirror a row when clothing contains readable or directional details. `GOAT Leo` has `10`, so generate `running-left` independently.

## Prepare

From repository root:

```bash
SKILL_DIR=.opencode/skills/hatch-pet
RUN_DIR=work/goat-leo

uv run python "$SKILL_DIR/scripts/prepare_pet_run.py" \
  --pet-name "GOAT Leo" \
  --pet-id goat-leo \
  --display-name "GOAT Leo" \
  --description "An iconic left-footed footballer inspired by Lionel Messi's 2022 world-champion era, featuring close control, creative passing, clinical finishing, and his sky-point celebration. Unofficial fan-made pet; not affiliated with or endorsed by Lionel Messi, any federation, or any club." \
  --pet-notes "$(cat pets/goat-leo/identity.txt)" \
  --style-preset pixel \
  --style-notes "full-resolution 192x208 pixel illustration, crisp fixed dark outline, controlled antialiasing, no forced 2x pixel blocks" \
  --state-overrides-file pets/goat-leo/state-overrides.json \
  --forbid-running-left-mirror \
  --output-dir "$RUN_DIR"
```

`prepare_pet_run.py` creates prompts, nine layout guides, decoded output paths, and `imagegen-jobs.json`. The base job is prompt-only; every row edit uses both canonical base and its layout guide.

## Generate

Use `.opencode/skills/imagegen/scripts/image_gen.py`. Every live command must include:

```text
--model gpt-image-2
--quality high
--ledger work/goat-leo/image-calls.json
--max-calls 100
```

Base generation uses `generate`. Row generation uses `edit`, with canonical base first and matching layout guide second. Use `--input-fidelity high`, `--output-format png`, and `--no-augment`; generated hatch prompts are already authoritative.

After accepting an output, copy it to the job's `decoded/` path and atomically update only that job in `imagegen-jobs.json`. For the selected base, also write `references/canonical-base.png`. Never record a signed response URL.

## Approval Gates

1. Generate at most three base candidates. Show them and stop until the user chooses one.
2. Generate `idle` and `running-right`. Build focused previews; stop for identity, number, ball, detail clarity, and gait approval.
3. Generate remaining rows. Build contact sheet and all nine GIFs; stop so the user can prioritize repairs.
4. After targeted repairs, build final atlas and package; stop for the user's manual OpenPets import.

No gate may be skipped. Rejected images still count if a live API request was made.

## Deterministic Pipeline

After all row strips are approved:

```bash
uv run python "$SKILL_DIR/scripts/extract_strip_frames.py" \
  --decoded-dir "$RUN_DIR/decoded" \
  --output-dir "$RUN_DIR/frames" \
  --states all \
  --chroma-key "#FF00FF" \
  --method auto

uv run python "$SKILL_DIR/scripts/inspect_frames.py" \
  --frames-root "$RUN_DIR/frames" \
  --json-out "$RUN_DIR/qa/review.json" \
  --require-components

uv run python "$SKILL_DIR/scripts/compose_atlas.py" \
  --frames-root "$RUN_DIR/frames" \
  --output "$RUN_DIR/final/spritesheet.png" \
  --webp-output "$RUN_DIR/final/spritesheet.webp" \
  --pixel-grid-scale 1

uv run python "$SKILL_DIR/scripts/validate_atlas.py" \
  "$RUN_DIR/final/spritesheet.webp" \
  --json-out "$RUN_DIR/final/validation.json" \
  --pixel-grid-scale 1

uv run python "$SKILL_DIR/scripts/make_contact_sheet.py" \
  "$RUN_DIR/final/spritesheet.webp" \
  --output "$RUN_DIR/qa/contact-sheet.png"

uv run python "$SKILL_DIR/scripts/render_animation_previews.py" \
  --frames-root "$RUN_DIR/frames" \
  --output-dir "$RUN_DIR/qa/previews"
```

If extraction alone causes size popping, retry `stable-slots` before spending another image call. Repair only failed rows.

## Package

Final runtime package root contains exactly:

```text
pet.json
spritesheet.webp
```

Write these under `dist/<pet-id>/`, then create `dist/<pet-id>.zip` without an enclosing directory. Copy only final thumbnail, contact sheet, and nine GIFs to `previews/<pet-id>/`.

## Acceptance

- Exact `1536x1872` WebP, 8x9 cells, 57 used frames.
- Unused cells fully transparent; transparent pixels have zero RGB residue.
- Every used cell preserves full 192x208 source detail with controlled antialiasing.
- Same face, hair, beard, body proportions, kit, `10`, shoes, and football in all frames.
- Football touches or overlaps the player; no detached components.
- No logos, crests, flags, brands, sponsors, other text, scenery, shadows, trails, glow, or chroma residue.
- `running-left` is independently generated and left-foot semantics remain correct.
- Deterministic validation passes, contact sheet and all GIFs receive visual review, then user confirms manual OpenPets import.

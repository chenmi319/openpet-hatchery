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
- `references/review-workflow.md` for existing-pet review or repair

Do not infer unresolved product choices. Do not use third-party reference photos unless the pet spec explicitly allows them.

## Hard Boundaries

- Use the sibling `imagegen` CLI for all generated visuals.
- Do not hand-paint anatomy or composite/rescale body parts to hide generation defects. Keep whole-frame extraction and shared-scale previews separate from visual repair.
- Run every paid call serially. Never use subagents or `generate-batch`.
- Record every paid request attempt in the call ledger; counts are statistics, not a budget cap. Never retry silently or skip approval gates.
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

`prepare_pet_run.py` creates prompts, nine layout guides, decoded output paths, and `imagegen-jobs.json`. The base job is prompt-only; initial row edits use canonical base and the row's layout guide. Targeted repairs follow the reference-role rules below.

## Generate

Use `.opencode/skills/imagegen/scripts/image_gen.py`. Every live command must include:

```text
--model gpt-image-2
--quality high
--ledger work/goat-leo/image-calls.json
```

Base generation uses `generate`. Initial row generation uses `edit`, with canonical base first and matching layout guide second. For a targeted masked repair, put the full edit target first so the mask applies to it; retain canonical identity, label each reference role, and omit conflicting or unnecessary references. Use `--input-fidelity high`, `--output-format png`, and `--no-augment`; generated hatch prompts are already authoritative.

After accepting an output, copy it to the job's `decoded/` path and atomically update only that job in `imagegen-jobs.json`. For the selected base, also write `references/canonical-base.png`. Never record a signed response URL.

## Approval Gates

1. Generate at most three base candidates. Show them and stop until the user chooses one.
2. Generate `idle` and `running-right`. Build focused previews; stop for identity, number, ball, detail clarity, and gait approval.
3. Generate remaining rows. Build a whole review candidate with a contact sheet, all nine normal/slow animations, a same-scale page, sources and known defects; stop for consolidated feedback. For an existing pet, start here using the best available rows rather than restarting base generation.
4. Within an approved repair stage, make delegated visual decisions without asking after every frame. Deliver complete affected-action previews and before/after comparison, updating the whole candidate when useful; stop at the stage boundary or on request error/no useful progress. Do not infer a new paid scope from delegated decisions.
5. After visual acceptance and explicit promotion authorization, build the final atlas and package; stop for the user's manual OpenPets import. A provisional review ZIP under `work/` is not promotion and may replace a same-ID pet if manually imported.

No gate may be skipped. Rejected images still count if a live API request was made.

Keep the edit narrow but assess the whole action. After two consecutive edits of the same defect without visible improvement, change the approach or pause rather than repeat near-identical prompts. Preserve the best full-action candidate instead of stacking repairs on regressions. See `references/review-workflow.md` for progress checkpoints and safe status recovery before any resend.

## Deterministic Pipeline

For a provisional whole-pet review, the same tools may build and check an explicitly unaccepted atlas under a separate `work/` directory; that does not accept rows or replace job outputs. Use row-scoped validation for incomplete previews. For production, run the following after all row strips are approved:

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

OpenPets v4.1.0 uses equal-time CSS steps. Previews follow that baseline with GIF 10ms rounding, not a longer last-frame pause. Use `--waiting-duration-ms 2200` only when reviewing the host's Relaxed waiting setting. QA GIFs loop continuously; host waving/jumping/failed default to two iterations. Idle takes 5500ms, so a whole closed-eye frame is not a brief blink.

Row names identify host states, not mandatory poses: `review` is thinking, `running` is active work, and `jumping` is success. Approved character actions may use running or running celebration while staying within their slots. Do not combine these overrides with older no-running or mandatory-jump instructions.

## Package

This project's supported runtime package is a V1 WebP base pet without a wardrobe. Its root contains exactly:

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
- Check geometry at final sprite size and normal playback, including state transitions. No visible position/size pumping is required; exact pixel preservation or numerical tolerances must be agreed explicitly. Masks do not guarantee unedited geometry stays fixed, and format/browser-function checks do not replace visual or host acceptance.
- By default the football touches or overlaps the player; any brief separation requires the approved close-control exception below.
- For an explicitly approved close-control running or celebration design, the canonical ball may briefly separate from the boot while staying near the player and visible. Retain it in the same frame during extraction; unrelated detached effects remain forbidden. Existing accepted assets are not replaced merely because the rule changes.
- No logos, crests, flags, brands, sponsors, other text, scenery, shadows, trails, glow, or chroma residue.
- `running-left` is independently generated and left-foot semantics remain correct.
- Deterministic validation passes, contact sheet and all GIFs receive visual review, then user confirms manual OpenPets import.

## Compatibility and Future Wardrobes

Runtime baseline: OpenPets v4.1.0 at `963ad049fe08c465c822ee5cc7ff02e93f28b232`; see `references/codex-pet-contract.md`. V1 WebP remains supported. V2 gaze, SVG, and wardrobes are optional and not implemented by this pipeline.

A future wardrobe adds full alternate atlases for selected outfits using the same base layout and approved poses. It does not require converting V1 to V2 or redrawing the accepted base outfit. Lock actions, face/body proportions and ball design first; then add outfit assets and manifest/package validation together. Do not add incomplete outfit metadata now.

# GOAT Leo

## Identity

- ID: `goat-leo`
- Display name: `GOAT Leo`
- Format: OpenPets V1, 8 columns x 9 rows, 192x208 per cell
- Style: full-resolution 192x208 pixel illustration with crisp outlines and controlled antialiasing
- Reference policy: text-only canonical base; no third-party photos
- Positioning: respectful fan tribute, not parody

Canonical identity text lives in `identity.txt`. Animation actions live in `state-overrides.json`; these files are generation inputs and must stay synchronized with approved decisions.

## Description

> An iconic left-footed footballer inspired by Lionel Messi's 2022 world-champion era, featuring close control, creative passing, clinical finishing, and his sky-point celebration. Unofficial fan-made pet; not affiliated with or endorsed by Lionel Messi, any federation, or any club.

## Frame Contract

| Row | State | Frames | GOAT Leo action |
|---:|---|---:|---|
| 0 | idle | 6 | Breathing, blink, ball beside left boot |
| 1 | running-right | 8 | Close-control rightward dribble |
| 2 | running-left | 8 | Independent leftward dribble and inward cut |
| 3 | waving | 4 | Standard friendly wave |
| 4 | jumping | 5 | Light hop, landing, sky-point celebration |
| 5 | failed | 8 | Missed chance, quiet disappointment, recovery |
| 6 | waiting | 6 | First touch, sole on ball, scan |
| 7 | running | 6 | Stationary left-foot finishing cycle |
| 8 | review | 6 | Scan, open body, disguised left-foot pass |

Total used frames: 57. Unused cells must be fully transparent.

## Approval Gates

1. Select one canonical base from at most three candidates.
2. Approve `idle` and `running-right` identity and gait.
3. Review full contact sheet and nine GIFs; prioritize targeted repairs.
4. Approve final package after manual OpenPets import.

## Hard QA

- Same face, hair, beard, proportions, stripe layout, number `10`, shorts, socks, boots, and football in all frames.
- `10` is present, readable, not mirrored, and not replaced by another glyph.
- Football remains one canonical black-and-white design and touches the player in every frame.
- Left-foot dominance is visually consistent.
- No crop, cell overlap, size pop, baseline jump, repeated static row, chroma fringe, hidden RGB residue, detached component, or forbidden mark.
- `running-left` must be generated independently.
- All deterministic checks and visual GIF review must pass before packaging.

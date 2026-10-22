# {{DISPLAY_NAME}}

## Identity

- ID: `{{PET_ID}}`
- Display name: `{{DISPLAY_NAME}}`
- Category: `{{CATEGORY}}`
- Format: OpenPets V1, 8 columns x 9 rows, 192x208 per cell
- Style: Full-resolution 192x208 pixel illustration with crisp outlines and controlled antialiasing
- Reference policy: text-only canonical base; no third-party copyrighted elements

Canonical identity text lives in `identity.txt`. Animation actions live in `state-overrides.json`; these files are generation inputs and must stay synchronized with approved decisions.

## Description

> {{DESCRIPTION}}

## Frame Contract

| Row | State | Frames | {{DISPLAY_NAME}} Action |
|---:|---|---:|---|
| 0 | idle | 6 | Calm loop: subtle breathing, natural eye blink, small idle gesture |
| 1 | running-right | 8 | Active rightward locomotion with alternating strides |
| 2 | running-left | 8 | Active leftward locomotion (independently drawn; do not mirror if directional details exist) |
| 3 | waving | 4 | Friendly greeting gesture towards viewer |
| 4 | jumping | 5 | Vertical jump, celebration or excited leap |
| 5 | failed | 8 | Disappointment or missed attempt reaction, settling into resolute recovery |
| 6 | waiting | 6 | Thoughtful paused pose, rhythmic idle waiting cycle |
| 7 | running | 6 | Forward-facing running or active stationary work loop |
| 8 | review | 6 | Inspection, scanning or thoughtful observation loop |

Total used frames: 57. Unused cells must be fully transparent RGBA (0, 0, 0, 0).

## Hard QA Rules

- Strict character identity: same face, hair, outfit, accessories, and colors in all frames.
- Standard geometry: head width and height proportions strictly aligned across all 9 rows.
- No cell overlap, vertical baseline jump, repeated static rows, chroma residue, or cutoffs.
- All 22 deterministic pipeline checks must pass before packaging.

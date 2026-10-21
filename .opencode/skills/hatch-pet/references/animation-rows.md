# Animation Rows

This project outputs V1: 8 columns, 9 rows, 192x208 pixels per cell. OpenPets v4.1.0 also supports optional V2 gaze rows, outside this pipeline. Runtime timing is host-owned and each row uses equal-time CSS steps.

| Row | State | Used columns | Durations |
| --- | --- | ---: | --- |
| 0 | idle | 0-5 | 5500 ms per cycle |
| 1 | running-right | 0-7 | 1060 ms per cycle |
| 2 | running-left | 0-7 | 1060 ms per cycle |
| 3 | waving | 0-3 | 700 ms per cycle, twice |
| 4 | jumping | 0-4 | 840 ms per cycle, twice |
| 5 | failed | 0-7 | 1220 ms per cycle, twice |
| 6 | waiting | 0-5 | 1010 ms Normal / 2200 ms Relaxed |
| 7 | running | 0-5 | 820 ms per cycle |
| 8 | review | 0-5 | 1030 ms per cycle |

Unused cells after each row's final used column must be fully transparent.

## Row Purposes

- `idle`: calm, low-distraction breathing/blinking loop; use as the reduced-motion first frame. Keep motion subtle and persona-preserving.
- `running-right`: locomotion to the right; 8-frame loop should read directionally.
- `running-left`: mirrored or redrawn locomotion to the left; do not simply reuse right-facing frames unless the design is symmetric, and any mirror derivation must preserve frame order and timing semantics.
- `waving`: greeting or attention gesture; clear start, raised gesture, return.
- `jumping`: success/celebration; approved running celebration is allowed. Design for two cycles without requiring a separate entry animation.
- `failed`: error/sad/deflated reaction; readable but not visually noisy.
- `waiting`: patient waiting/testing/permission state; not an impatient repeated request gesture.
- `running`: active work/editing/execution; use the approved persona action, including running poses. Keep the torso anchored within its slot, without directional travel across the strip.
- `review`: focused/inspecting/thinking loop suitable for review state.

Default reactions: thinking→review; working/editing/running→running; testing/waiting→waiting; success/celebrating→jumping; error→failed; waving→waving; idle→idle. User overrides are host settings, not custom FPS fields in pet.json.

The OpenCode plugin 4.1.0 automatically emits thinking on prompt, editing before named write/edit/patch tools, testing before test-like shell commands, waiting for permissions, success on session.idle and error on execution failure. These six reactions use five distinct rows; with host idle there are six main animations. Ordinary reads/search/non-test shell do not proactively send working. Waving and directional motion are not automatic plugin events.

GIFs round cumulative frame boundaries to 10ms while keeping the exact cycle total. They loop for QA even when the host reaction is finite. Do not judge a brief blink from a long full-eye-closed Idle frame.

Source: OpenPets v4.1.0 `apps/desktop/src/reaction-animation-mapping.ts`, `pet-window-styles.ts`, `app-state-core.ts` at commit `963ad049fe08c465c822ee5cc7ff02e93f28b232`; plugin `@open-pets/opencode@4.1.0/dist/opencode-plugin-runtime.js`.

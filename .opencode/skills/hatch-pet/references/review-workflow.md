# Whole-Pet Review and Targeted Repair

## Review the usable version first

For an existing pet repair, assemble the best available nine-row candidate before spending calls on isolated defects. Keep accepted rows and historical candidates; do not regenerate sound rows merely to make a new version. A missing or rejected replacement may use an existing row for comparison only when its origin and unresolved defects are clearly labeled.

Deliver one review directory under `work/<pet-id>/` containing:

- An atlas, contact sheet and all nine normal-speed animations; add slow previews for diagnosis.
- One page showing every action at the same `192x208` display scale, with normal playback first.
- Per-row source and status: usable candidate, needs repair, or needs design change; distinguish these from final acceptance.
- Known defects and the scope of checks actually performed. Format validation does not establish gait, anatomy, identity or visual naturalness.

Use the expected V1 frame counts and host cycle durations. Do not duplicate frames, mirror readable details, reverse playback, shift whole sprites or change timing to fake a missing movement. Partial pose comparisons must be labeled as partial, not presented as complete loops.

An optional review ZIP stays under `work/`, uses the runtime root layout, and is explicitly provisional. Do not copy it into `dist/` or public previews. Warn that manual import with the same pet ID may replace the user's installed version; do not import or promote it without authorization.

## One feedback round, then action-sized repair

Ask the user to review the whole version once, marking each action usable / needs repair / change design and naming its most obvious defect. Prioritize visible identity or geometry failures, then recognizable movement and loop closure, then low-impact details. Keep unresolved product choices explicit.

When the user delegates visual decisions and approves a repair stage, complete that stage without asking after every frame or successful request. The paid scope still needs approval: which action or defect is being repaired, the intended result and the stage's stopping conditions. Delegation does not authorize unlimited unrelated work, installation, request retries or formal publication. Call counts remain statistics, not an automatic cumulative budget limit; honor any limit the user explicitly sets.

The stage ends with a complete affected-action animation, before/after comparison and an updated whole-pet candidate when useful. Stop early on a request error, a blocking design choice, or no useful visual progress. Report partial completion honestly rather than renaming another failed attempt a stage success.

## Keep edits narrow, evaluate the whole action

Use the smallest edit that fixes the root cause: one defective frame or local region when sufficient, otherwise the affected row. A small edit is not a reason to postpone reviewing the whole animation. After a successful request, quickly reject obvious extra limbs, wrong text, missing props or clipping; then build the complete action preview before pursuing micro-details.

Compare against the best prior full-action candidate. If an edit introduces regressions, keep the better candidate and do not repeatedly repair the newly broken image by default. After two consecutive edits of the same defect without visible improvement, change the reference/pose organization or pause with a clear limitation; changing a few prompt words alone is not a new approach. This is a progress checkpoint, not a total call cap.

Reuse the existing extraction, composition, preview and validation tools. Keep per-attempt prompts and decisions as data; avoid creating a new runner or renderer for every revision. Group related checks at stage delivery, and do not repeatedly run unchanged whole-project checks during asset repair.

## Set perceptual geometry requirements explicitly

Judge consistency at final sprite size and normal cycle speed, across frames and state transitions. "No visible size pumping or position drift" must not silently become zero changed pixels. Use original-scale measurements to diagnose a visible defect, recording exactly which region and property were measured; do not infer full anatomy from a bounding box that includes the ball or an occupied crop window.

For an in-place run, preserve the same camera, head/torso/hip size and anchors, and prop scale. Do not create running by camera travel or body scaling. Frame-wide changes to placement or scale must not be hidden by independent per-frame or per-group normalization. Shared viewports and shared preview scale are allowed; manual body-part resizing or compositing is not a substitute for a correct generated pose. This project's generated visual repairs use `imagegen`, not hand-painted anatomy.

If a strict numerical tolerance or exact pixel preservation is required, agree it before accepting the edit. A mask guides an edit; it does not prove that unmasked geometry or pixels stayed unchanged. Verify the requested invariants from the actual output. RGB differences alone do not measure motion, because colors and antialiasing may change without geometric drift.

## Ground one edit, avoid conflicting references

Follow the sibling `imagegen` skill. Label each image's role: edit target, canonical identity, layout only, appearance/size reference, or motion reference. Do not ask an appearance reference to dictate the opposite leg's pose. Use only references needed for the current defect; more references are not automatically better.

Start new row edits with canonical identity and the matching layout guide. For a targeted masked edit, the full edit target must be the first image paired with the mask; keep canonical identity attached and omit an unnecessary guide or motion reference if it conflicts with the task. Never assume a layout outline will disappear: inspect the output.

## Recover results safely

Record an attempt before sending. Use serial calls and keep SDK retries disabled. When a result notification arrives, read the saved status and output before the next request. If the user asks about progress or requests a resend, make one local status/output check rather than claiming the request is still running from an old message.

- Successful status and saved image: review that result; do not resend.
- Failed request: stop; a retry requires explicit authorization.
- Started/interrupted status or missing output: outcome and billing may be unknown. Preserve the ledger, explain uncertainty, and do not blindly resend. Do not poll repeatedly.

## Verify and promote separately

At stage delivery, check the affected complete row's counts, dimensions, transparency and timing. For a whole candidate, check all 57 frames and the atlas; validate ZIP structure if supplied. Use a row-scoped check for a one-row preview, not the nine-row checker against an intentionally incomplete directory. Never claim a failed or unexecuted check passed.

Use an available browser tool to verify the current page's loading, order and controls when useful; do not install or enable a missing tool to bypass authorization. Browser events or screenshots do not by themselves establish continuous visual naturalness. Record separately: format checks, browser functionality, visual acceptance, and actual host import.

Only visually accepted replacements may enter accepted decoded job outputs. Update the corresponding job atomically, not the entire manifest. Keep stable specifications and final assets unchanged until the design and promotion scope are confirmed; synchronize the specifications when promoting the new design. Host import, Git writes and Gallery publication remain separate approval gates.

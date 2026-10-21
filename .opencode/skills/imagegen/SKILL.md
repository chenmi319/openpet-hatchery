---
name: imagegen
description: Generate or edit raster images through this repository's private OpenAI-compatible Images API adapter. Use for hatch-pet base sprites and grounded animation-row edits after the user approves a paid generation gate.
license: Apache-2.0
compatibility: OpenCode project skill; requires Python 3.11+, uv, openai, Pillow, and an ignored local proxy JSON file.
metadata:
  upstream: openai/skills@49f948faa9258a0c61caceaf225e179651397431
---

# Imagegen

Use bundled `scripts/image_gen.py`. This project has no built-in image tool and does not use Codex runtime paths.

## Runtime Contract

Live calls read the ignored repository-local file `.imagegen.local.json`:

```json
{
  "baseUrl": "https://your-private-image-api.example/v1",
  "apiKeyFile": "~/.secrets/your-image-api-key"
}
```

Copy `.imagegen.local.example.json` to create it. `apiKeyFile` points to a separate local secret file. Never print either value, copy the local file into tracked output, pass the key as a command argument, or use `OPENAI_API_KEY`.

The adapter deliberately fails when the local file or either field is absent. Never fall back to environment variables or the SDK's official default endpoint.

## Project Defaults

Model compatibility experiment: `--model "Nano Banana 2.1" --quality auto` is supported through the configured OpenAI-compatible endpoint. This adapter uses a conservative, tested parameter profile, not a universal statement about all providers: omit mask, background, output-format, output-compression, input-fidelity and moderation; these requests are rejected locally, not silently stripped. Limit prompts to 4000 characters, references to 14, and output to one image. The service selects the output format; verify decoded file format rather than trusting the `.png` filename. This is not native transparency support or a replacement for the default GPT pet-production workflow. Paid experiments still need explicit approval.

```text
model: gpt-image-2
quality: high
live calls: counted as request attempts, no cumulative cap
execution: serial only
response forms: b64_json or HTTPS URL
```

Every live command requires `--ledger`. The adapter records an attempt before the request because a disconnected request may still be charged. Counts are statistics, not successful images or verified billing. Never remove failed entries without explicit user approval. `--max-calls` and legacy config `maxCalls` are accepted only for compatibility, warn and do not impose a limit. Each batch still needs explicit user approval and remains serial.

SDK automatic retries are disabled so one ledger reservation cannot silently send multiple paid requests. A failed call requires explicit approval before retrying.

For pet repairs, follow `../hatch-pet/references/review-workflow.md`: approve the action/defect and stage scope, then make delegated visual decisions without per-frame questions. Keep calls serial, review the complete affected action and deliver a stage comparison. Repeated edits without visible progress require a different approach or a pause, not unlimited prompt retries; counts alone neither stop authorized work nor authorize more work.

Before resending after a missing notification or progress query, check local status and saved output once. A successful result with an image must be reviewed rather than sent again. A started/interrupted request can have unknown completion and billing; preserve its ledger entry, explain uncertainty and require explicit authorization before a retry. Do not poll repeatedly.

## Commands

Generate one image:

```bash
uv run python .opencode/skills/imagegen/scripts/image_gen.py generate \
  --prompt-file /absolute/path/to/prompt.md \
  --model gpt-image-2 \
  --quality high \
  --output-format png \
  --no-augment \
  --ledger /absolute/path/to/image-calls.json \
  --out /absolute/path/to/output.png
```

Edit with grounded inputs:

```bash
uv run python .opencode/skills/imagegen/scripts/image_gen.py edit \
  --prompt-file /absolute/path/to/prompt.md \
  --image /absolute/path/to/canonical-base.png \
  --image /absolute/path/to/layout-guide.png \
  --input-fidelity high \
  --model gpt-image-2 \
  --quality high \
  --output-format png \
  --no-augment \
  --ledger /absolute/path/to/image-calls.json \
  --out /absolute/path/to/output.png
```

Use `--dry-run` for no-cost validation. Dry-run does not require the local runtime file and never changes the ledger.

Label each image as edit target, identity, layout, appearance/size or motion reference; avoid conflicting references. When using `edit --mask`, put the full edit target first so the mask applies to that image, retaining canonical identity as a reference. A mask does not promise unchanged pixels or geometry outside the region: compare the actual result against the requested invariants, and do not composite original body parts back to fake preservation.

## Safety Rules

- Do not use `generate-batch`; the adapter disables it.
- One command produces one candidate. Do not set `--n` above 1.
- Do not overwrite accepted images unless the user approved replacement; use candidate filenames.
- Do not expose response URLs. The adapter validates HTTPS, rejects non-public destinations and redirects, enforces 50MB, checks image signatures, then saves bytes.
- Keep prompts free of secrets and third-party image URLs.
- Use `generate` only for prompt-only base candidates. Use `edit` for every animation row so canonical identity remains attached.
- Report output path and ledger count, not API payloads or URLs.

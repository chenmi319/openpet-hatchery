---
name: imagegen
description: Generate or edit raster images through this repository's private OpenAI-compatible Images API adapter. Use for hatch-pet base sprites and grounded animation-row edits after the user approves a paid generation gate.
license: Apache-2.0
compatibility: OpenCode project skill; requires Python 3.11+, uv, openai, Pillow, and runtime proxy variables.
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

```text
model: gpt-image-2
quality: high
maximum live calls: 100
execution: serial only
response forms: b64_json or HTTPS URL
```

Every live command requires `--ledger` and `--max-calls 100`. The adapter reserves a ledger entry before the request because a disconnected request may still be charged. Never edit the ledger to reclaim a failed call without explicit user approval.

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
  --max-calls 100 \
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
  --max-calls 100 \
  --out /absolute/path/to/output.png
```

Use `--dry-run` for no-cost validation. Dry-run does not require the local runtime file and never changes the ledger.

## Safety Rules

- Do not use `generate-batch`; the adapter disables it.
- One command produces one candidate. Do not set `--n` above 1.
- Do not overwrite accepted images unless the user approved replacement; use candidate filenames.
- Do not expose response URLs. The adapter validates HTTPS, rejects non-public destinations and redirects, enforces 50MB, checks image signatures, then saves bytes.
- Keep prompts free of secrets and third-party image URLs.
- Use `generate` only for prompt-only base candidates. Use `edit` for every animation row so canonical identity remains attached.
- Report output path and ledger count, not API payloads or URLs.

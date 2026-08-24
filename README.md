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

Live image generation uses a local ignored file. Create it from the example:

```bash
cp .imagegen.local.example.json .imagegen.local.json
```

Set its private `baseUrl` and `apiKeyFile` path. The key remains in the separate secret file. The adapter fails closed when the local config or either field is absent; it never reads proxy settings from the OpenCode environment and never falls back to the official OpenAI endpoint.

Restart OpenCode after cloning or changing files under `.opencode/skills/`, then ask it to use `hatch-pet` for a pet specification under `pets/`.

## Validation

No-cost checks:

```bash
uv run python -m compileall -q .opencode scripts tests
uv run python -m unittest discover -s tests -v
uv run python .opencode/skills/imagegen/scripts/image_gen.py generate \
  --prompt "dry run" \
  --dry-run \
  --out work/dry-run.png
```

Final packages are imported manually into OpenPets before any Git or Gallery publication.

## Licensing

Code and vendored skill derivatives use Apache-2.0; see `LICENSE` and `UPSTREAM.md`. Generated pet assets have separate terms in `ASSET-LICENSE.md`.

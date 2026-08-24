#!/usr/bin/env python3
"""Validate and package exactly one OpenPets V1 pet directory."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

from PIL import Image

REQUIRED_FILES = {"pet.json", "spritesheet.webp"}
PET_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
ATLAS_SIZE = (1536, 1872)


def validate_pet(pet_dir: Path) -> None:
    files = {path.name for path in pet_dir.iterdir() if path.is_file()}
    if files != REQUIRED_FILES:
        raise ValueError(f"pet directory must contain exactly {sorted(REQUIRED_FILES)}; got {sorted(files)}")

    metadata = json.loads((pet_dir / "pet.json").read_text(encoding="utf-8"))
    required = {"id", "displayName", "description", "spritesheetPath"}
    missing = sorted(required - set(metadata))
    if missing:
        raise ValueError(f"pet.json missing fields: {', '.join(missing)}")
    if not PET_ID.fullmatch(metadata["id"]):
        raise ValueError("pet id is invalid")
    if metadata["spritesheetPath"] != "spritesheet.webp":
        raise ValueError("spritesheetPath must be spritesheet.webp")

    with Image.open(pet_dir / "spritesheet.webp") as image:
        if image.format != "WEBP" or image.size != ATLAS_SIZE:
            raise ValueError(f"spritesheet must be a {ATLAS_SIZE[0]}x{ATLAS_SIZE[1]} WebP")
        if "A" not in image.getbands():
            raise ValueError("spritesheet must contain alpha")


def package_pet(pet_dir: Path, output: Path) -> None:
    validate_pet(pet_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    # OpenPets 从 ZIP 根目录校验文件；多包一层 Pet 目录会让安装包失效。
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(REQUIRED_FILES):
            archive.write(pet_dir / name, arcname=name)
    temporary.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pet_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    pet_dir = args.pet_dir.expanduser().resolve()
    if not pet_dir.is_dir():
        raise SystemExit(f"pet directory not found: {pet_dir}")
    if args.check_only:
        validate_pet(pet_dir)
        print(f"valid: {pet_dir}")
        return
    package_pet(pet_dir, args.output.expanduser().resolve())
    print(f"wrote {args.output.expanduser().resolve()}")


if __name__ == "__main__":
    main()

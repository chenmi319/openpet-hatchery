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
# 对齐 v4.1.0 导入边界；本工具仅打包无衣橱的 V1 WebP 基础包。
MAX_METADATA_BYTES = 128 * 1024
MAX_ATLAS_BYTES = 100 * 1024 * 1024
MAX_ZIP_BYTES = 50 * 1024 * 1024


def validate_pet(pet_dir: Path) -> None:
    if pet_dir.is_symlink() or not pet_dir.is_dir():
        raise ValueError("pet directory must be a regular directory, not a symlink")
    entries = list(pet_dir.iterdir())
    files = {path.name for path in entries}
    if files != REQUIRED_FILES:
        raise ValueError(f"pet directory must contain exactly {sorted(REQUIRED_FILES)}; got {sorted(files)}")
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise ValueError("pet package entries must be regular files, not directories or symlinks")
    if (pet_dir / "pet.json").stat().st_size > MAX_METADATA_BYTES:
        raise ValueError("pet.json exceeds the 128 KiB limit")
    if (pet_dir / "spritesheet.webp").stat().st_size > MAX_ATLAS_BYTES:
        raise ValueError("spritesheet exceeds the 100 MiB limit")

    metadata = json.loads((pet_dir / "pet.json").read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("pet.json must be an object")
    required = {"id", "displayName", "description", "spritesheetPath"}
    missing = sorted(required - set(metadata))
    if missing:
        raise ValueError(f"pet.json missing fields: {', '.join(missing)}")
    if not isinstance(metadata["id"], str) or not PET_ID.fullmatch(metadata["id"]) or metadata["id"] == "builtin":
        raise ValueError("pet id is invalid")
    for field, limit in (("displayName", 80), ("description", 500)):
        value = metadata[field]
        # 宿主 JavaScript length 按 UTF-16 计数，非 BMP 字符占两个单元。
        if not isinstance(value, str) or not value.strip() or len(value.encode("utf-16-le")) // 2 > limit:
            raise ValueError(f"{field} must be non-empty and at most {limit} UTF-16 code units")
    if "spriteVersionNumber" in metadata or "wardrobe" in metadata:
        raise ValueError("this packager supports only unmarked V1 pets without a wardrobe")
    if metadata["spritesheetPath"] != "spritesheet.webp":
        raise ValueError("spritesheetPath must be spritesheet.webp")

    with Image.open(pet_dir / "spritesheet.webp") as image:
        if image.format != "WEBP" or image.size != ATLAS_SIZE:
            raise ValueError(f"spritesheet must be a {ATLAS_SIZE[0]}x{ATLAS_SIZE[1]} WebP")
        if "A" not in image.getbands():
            raise ValueError("spritesheet must contain alpha")
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError("spritesheet must contain exactly one image")
        image.load()


def package_pet(pet_dir: Path, output: Path) -> None:
    validate_pet(pet_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    # OpenPets 从 ZIP 根目录校验文件；多包一层 Pet 目录会让安装包失效。
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(REQUIRED_FILES):
            archive.write(pet_dir / name, arcname=name)
    if temporary.stat().st_size > MAX_ZIP_BYTES:
        temporary.unlink()
        raise ValueError("pet ZIP exceeds the 50 MiB limit")
    temporary.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pet_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    pet_dir = args.pet_dir.expanduser().absolute()
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

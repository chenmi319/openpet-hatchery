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
OUTFIT_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
ATLAS_SIZE = (1536, 1872)
# 对齐 v4.1.0 导入边界；支持无衣橱基础包与带 outfits/ 的衣橱包。
MAX_METADATA_BYTES = 128 * 1024
MAX_ATLAS_BYTES = 100 * 1024 * 1024
MAX_ZIP_BYTES = 50 * 1024 * 1024


def _validate_atlas_file(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"atlas file not found: {path}")
    if path.stat().st_size > MAX_ATLAS_BYTES:
        raise ValueError(f"{path.name} exceeds the 100 MiB limit")
    with Image.open(path) as image:
        if image.format != "WEBP" or image.size != ATLAS_SIZE:
            raise ValueError(f"{path.name} must be a {ATLAS_SIZE[0]}x{ATLAS_SIZE[1]} WebP")
        if "A" not in image.getbands():
            raise ValueError(f"{path.name} must contain alpha")
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError(f"{path.name} must contain exactly one image")
        image.load()


def validate_pet(pet_dir: Path) -> None:
    if pet_dir.is_symlink() or not pet_dir.is_dir():
        raise ValueError("pet directory must be a regular directory, not a symlink")
    entries = list(pet_dir.iterdir())
    names = {path.name for path in entries}

    if (pet_dir / "pet.json").stat().st_size > MAX_METADATA_BYTES:
        raise ValueError("pet.json exceeds the 128 KiB limit")

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
    if "spriteVersionNumber" in metadata:
        raise ValueError("this packager supports only unmarked V1 pets")
    if metadata["spritesheetPath"] != "spritesheet.webp":
        raise ValueError("spritesheetPath must be spritesheet.webp")

    _validate_atlas_file(pet_dir / "spritesheet.webp")

    if "wardrobe" in metadata:
        wardrobe = metadata["wardrobe"]
        if not isinstance(wardrobe, dict):
            raise ValueError("wardrobe must be an object")
        outfits = wardrobe.get("outfits")
        if not isinstance(outfits, list) or not (1 <= len(outfits) <= 16):
            raise ValueError("wardrobe must contain 1-16 outfits")
        outfit_ids: set[str] = set()
        declared_files: set[str] = set()
        for outfit in outfits:
            if not isinstance(outfit, dict):
                raise ValueError("outfit must be an object")
            oid = outfit.get("id")
            if not isinstance(oid, str) or not OUTFIT_ID.fullmatch(oid) or oid in ("default", "auto") or oid in outfit_ids:
                raise ValueError(f"invalid outfit id: {oid}")
            outfit_ids.add(oid)
            name = outfit.get("displayName")
            if not isinstance(name, str) or not name.strip() or len(name.encode("utf-16-le")) // 2 > 40:
                raise ValueError("outfit displayName must be 1-40 UTF-16 code units")
            expected_path = f"outfits/{oid}.webp"
            if outfit.get("spritesheetPath") != expected_path:
                raise ValueError(f"outfit spritesheetPath must be {expected_path}")
            declared_files.add(f"{oid}.webp")
            _validate_atlas_file(pet_dir / expected_path)

        outfits_dir = pet_dir / "outfits"
        if not outfits_dir.is_dir() or outfits_dir.is_symlink():
            raise ValueError("outfits must be a directory")
        actual_files = {p.name for p in outfits_dir.iterdir()}
        if actual_files != declared_files:
            raise ValueError(f"outfits directory must contain exactly {sorted(declared_files)}; got {sorted(actual_files)}")
        if any(p.is_symlink() or not p.is_file() for p in outfits_dir.iterdir()):
            raise ValueError("outfits files must be regular files")

        expected_names = REQUIRED_FILES | {"outfits"}
    else:
        expected_names = REQUIRED_FILES

    if names != expected_names:
        raise ValueError(f"pet directory must contain exactly {sorted(expected_names)}; got {sorted(names)}")
    for path in entries:
        if path.name == "outfits":
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("pet package entries must be regular files, not directories or symlinks")


def package_pet(pet_dir: Path, output: Path, strip_wardrobe: bool = False) -> None:
    validate_pet(pet_dir)
    metadata = json.loads((pet_dir / "pet.json").read_text(encoding="utf-8"))
    has_wardrobe = "wardrobe" in metadata

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    # OpenPets 从 ZIP 根目录校验文件；多包一层 Pet 目录会让安装包失效。
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if has_wardrobe and not strip_wardrobe:
            archive.write(pet_dir / "pet.json", arcname="pet.json")
            archive.write(pet_dir / "spritesheet.webp", arcname="spritesheet.webp")
            for outfit in metadata["wardrobe"]["outfits"]:
                rel_path = outfit["spritesheetPath"]
                archive.write(pet_dir / rel_path, arcname=rel_path)
        else:
            if has_wardrobe and strip_wardrobe:
                base_meta = dict(metadata)
                del base_meta["wardrobe"]
                archive.writestr("pet.json", json.dumps(base_meta, indent=2) + "\n")
            else:
                archive.write(pet_dir / "pet.json", arcname="pet.json")
            archive.write(pet_dir / "spritesheet.webp", arcname="spritesheet.webp")

    if temporary.stat().st_size > MAX_ZIP_BYTES:
        temporary.unlink()
        raise ValueError("pet ZIP exceeds the 50 MiB limit")
    temporary.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pet_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--strip-wardrobe", action="store_true", help="strip wardrobe from package")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    pet_dir = args.pet_dir.expanduser().absolute()
    if not pet_dir.is_dir():
        raise SystemExit(f"pet directory not found: {pet_dir}")
    if args.check_only:
        validate_pet(pet_dir)
        print(f"valid: {pet_dir}")
        return
    package_pet(pet_dir, args.output.expanduser().resolve(), strip_wardrobe=args.strip_wardrobe)
    print(f"wrote {args.output.expanduser().resolve()}")


if __name__ == "__main__":
    main()

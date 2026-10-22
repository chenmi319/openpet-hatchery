#!/usr/bin/env python3
"""OpenPet Hatchery: Unified CLI for managing, scaffolding, validating, and packaging OpenPets pets."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PETS_DIR = ROOT / "pets"
DIST_DIR = ROOT / "dist"
PREVIEWS_DIR = ROOT / "previews"
TEMPLATE_DIR = PETS_DIR / "_template"

OUTFIT_ID_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PET_ID_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def cmd_list(args: argparse.Namespace) -> int:
    """List all pets and their release packages in the hatchery."""
    print("OpenPet Hatchery · Managed Pets\n" + "=" * 65)
    
    # Collect all pet directories from pets/ and dist/
    pet_ids: set[str] = set()
    if PETS_DIR.is_dir():
        for p in PETS_DIR.iterdir():
            if p.is_dir() and not p.name.startswith(("_", ".")):
                pet_ids.add(p.name)
    if DIST_DIR.is_dir():
        for p in DIST_DIR.iterdir():
            if p.is_dir() and not p.name.startswith(("_", ".")) and (p / "pet.json").is_file():
                pet_ids.add(p.name)
                
    if not pet_ids:
        print("No pets found. Use 'hatchery new <pet-id>' to create one.")
        return 0

    for pet_id in sorted(pet_ids):
        dist_pet = DIST_DIR / pet_id
        spec_file = PETS_DIR / pet_id / "spec.md"
        zip_file = DIST_DIR / f"{pet_id}.zip"
        
        display_name = pet_id
        outfits_list: list[str] = []
        category = "unknown"
        
        if (dist_pet / "pet.json").is_file():
            try:
                meta = json.loads((dist_pet / "pet.json").read_text(encoding="utf-8"))
                display_name = meta.get("displayName", pet_id)
                category = meta.get("category", "unknown")
                if "wardrobe" in meta and isinstance(meta["wardrobe"], dict):
                    for o in meta["wardrobe"].get("outfits", []):
                        outfits_list.append(f"{o.get('displayName', o.get('id'))} ({o.get('id')})")
            except Exception:
                pass
        elif spec_file.is_file():
            for line in spec_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("- Display name:"):
                    display_name = line.split(":", 1)[1].strip(" `")
                    break

        zip_info = "Not packaged"
        if zip_file.is_file():
            size_mb = zip_file.stat().st_size / (1024 * 1024)
            zip_info = f"dist/{pet_id}.zip ({size_mb:.2f} MB)"

        total_kits = 1 + len(outfits_list)
        default_outfit_title = "Default Outfit"
        if (dist_pet / "pet.json").is_file():
            try:
                meta = json.loads((dist_pet / "pet.json").read_text(encoding="utf-8"))
                if "defaultOutfitName" in meta:
                    default_outfit_title = f"{meta['defaultOutfitName']} (Default)"
            except Exception:
                pass

        print(f"• [{pet_id}] {display_name} (Category: {category})")
        print(f"  - Wardrobe Kits ({total_kits} total):")
        print(f"    1. {default_outfit_title} (spritesheet.webp)")
        for idx, o_name in enumerate(outfits_list, start=2):
            print(f"    {idx}. {o_name}")
        print(f"  - Package: {zip_info}")
        print(f"  - Spec Dir: {'pets/' + pet_id if (PETS_DIR / pet_id).is_dir() else 'missing'}")
        print()
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    """Scaffold a new pet specification from template."""
    pet_id = args.pet_id.strip().lower()
    if not PET_ID_REGEX.fullmatch(pet_id):
        print(f"Error: Invalid pet ID '{pet_id}'. Must be lowercase alphanumeric with hyphens (e.g. 'cyber-cat').", file=sys.stderr)
        return 1

    target_dir = PETS_DIR / pet_id
    if target_dir.exists():
        print(f"Error: Pet specification directory already exists: {target_dir}", file=sys.stderr)
        return 1

    display_name = args.name.strip() if args.name else pet_id.replace("-", " ").title()
    category = args.category.strip() if args.category else "mascots"
    description = args.desc.strip() if args.desc else f"An adorable pixel pet named {display_name}."

    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy and render templates
    for filename in ("identity.txt", "spec.md", "state-overrides.json"):
        src = TEMPLATE_DIR / filename
        if not src.is_file():
            print(f"Error: Template file missing: {src}", file=sys.stderr)
            return 1
        content = src.read_text(encoding="utf-8")
        content = content.replace("{{PET_ID}}", pet_id)
        content = content.replace("{{DISPLAY_NAME}}", display_name)
        content = content.replace("{{CATEGORY}}", category)
        content = content.replace("{{DESCRIPTION}}", description)
        (target_dir / filename).write_text(content, encoding="utf-8")

    # Also scaffold starter dist/<pet_id>/pet.json
    dist_pet = DIST_DIR / pet_id
    dist_pet.mkdir(parents=True, exist_ok=True)
    starter_meta = {
        "id": pet_id,
        "displayName": display_name,
        "description": description,
        "spritesheetPath": "spritesheet.webp",
        "category": category,
        "subcategory": "mascots",
        "sourceUrl": f"https://github.com/chenmi319/openpet-hatchery/tree/main/pets/{pet_id}",
        "wardrobe": {
            "outfits": [],
            "schedule": []
        }
    }
    (dist_pet / "pet.json").write_text(json.dumps(starter_meta, indent=2) + "\n", encoding="utf-8")

    print(f"✓ Successfully initialized new pet '{display_name}' ({pet_id})!")
    print(f"  - Specification: pets/{pet_id}/spec.md")
    print(f"  - Identity Text: pets/{pet_id}/identity.txt")
    print(f"  - State Prompts: pets/{pet_id}/state-overrides.json")
    print(f"  - Runtime Meta : dist/{pet_id}/pet.json")
    print("\nNext: Edit pets/{}/identity.txt and run 'hatch-pet' skill to begin generating sprites!".format(pet_id))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate pet atlases and package structures."""
    targets: list[str] = []
    if args.pet_id:
        targets.append(args.pet_id)
    else:
        if DIST_DIR.is_dir():
            for p in sorted(DIST_DIR.iterdir()):
                if p.is_dir() and (p / "pet.json").is_file():
                    targets.append(p.name)

    if not targets:
        print("No pets to validate in dist/.")
        return 0

    all_passed = True
    for pet_id in targets:
        pet_dir = DIST_DIR / pet_id
        zip_file = DIST_DIR / f"{pet_id}.zip"
        print(f"\nValidating [{pet_id}] ...")
        
        # 1. Package structure check
        if zip_file.is_file():
            chk = subprocess.run([
                sys.executable, str(ROOT / "scripts/package_pet.py"), "--check-only",
                str(pet_dir), str(zip_file)
            ], capture_output=True, text=True)
            if chk.returncode != 0:
                print(f"  ✗ Package integrity failed:\n{chk.stderr}")
                all_passed = False
            else:
                print(f"  ✓ Package integrity: OK ({zip_file.name})")
        else:
            print(f"  ⚠ dist/{pet_id}.zip not found (run 'hatchery package {pet_id}' first)")

        # 2. Atlas pixel check on spritesheet.webp
        base_atlas = pet_dir / "spritesheet.webp"
        if base_atlas.is_file():
            val = subprocess.run([
                sys.executable, str(ROOT / ".opencode/skills/hatch-pet/scripts/validate_atlas.py"),
                str(base_atlas), "--pixel-grid-scale", "1"
            ], capture_output=True, text=True)
            if '"ok": true' in val.stdout:
                print("  ✓ Base atlas (spritesheet.webp): Valid (0 errors, 0 residue)")
            else:
                print(f"  ✗ Base atlas invalid:\n{val.stdout}")
                all_passed = False

        # 3. Check wardrobe atlases
        outfits_dir = pet_dir / "outfits"
        if outfits_dir.is_dir():
            for outfit_webp in sorted(outfits_dir.glob("*.webp")):
                val = subprocess.run([
                    sys.executable, str(ROOT / ".opencode/skills/hatch-pet/scripts/validate_atlas.py"),
                    str(outfit_webp), "--pixel-grid-scale", "1"
                ], capture_output=True, text=True)
                if '"ok": true' in val.stdout:
                    print(f"  ✓ Wardrobe outfit ({outfit_webp.name}): Valid (0 errors, 0 residue)")
                else:
                    print(f"  ✗ Wardrobe outfit ({outfit_webp.name}) invalid:\n{val.stdout}")
                    all_passed = False

    return 0 if all_passed else 1


def cmd_package(args: argparse.Namespace) -> int:
    """Package one or all pets into dist/<pet-id>.zip."""
    targets: list[str] = []
    if args.pet_id:
        targets.append(args.pet_id)
    else:
        if DIST_DIR.is_dir():
            for p in sorted(DIST_DIR.iterdir()):
                if p.is_dir() and (p / "pet.json").is_file():
                    targets.append(p.name)

    if not targets:
        print("No pets to package in dist/.")
        return 0

    for pet_id in targets:
        pet_dir = DIST_DIR / pet_id
        zip_file = DIST_DIR / f"{pet_id}.zip"
        print(f"Packaging [{pet_id}] -> {zip_file} ...")
        cmd = [sys.executable, str(ROOT / "scripts/package_pet.py")]
        if args.strip_wardrobe:
            cmd.append("--strip-wardrobe")
        cmd.extend([str(pet_dir), str(zip_file)])
        subprocess.run(cmd, check=True)
        size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"✓ Packaged {zip_file.name} ({size_mb:.2f} MB)")
    return 0


def cmd_add_outfit(args: argparse.Namespace) -> int:
    """Register a new wardrobe outfit in dist/<pet-id>/pet.json."""
    pet_id = args.pet_id.strip()
    outfit_id = args.outfit_id.strip().lower()
    
    if not OUTFIT_ID_REGEX.fullmatch(outfit_id):
        print(f"Error: Invalid outfit ID '{outfit_id}'. Must be lowercase alphanumeric with hyphens.", file=sys.stderr)
        return 1

    pet_json_path = DIST_DIR / pet_id / "pet.json"
    if not pet_json_path.is_file():
        print(f"Error: pet.json not found for pet '{pet_id}' at {pet_json_path}", file=sys.stderr)
        return 1

    meta = json.loads(pet_json_path.read_text(encoding="utf-8"))
    if "wardrobe" not in meta or not isinstance(meta["wardrobe"], dict):
        meta["wardrobe"] = {"outfits": [], "schedule": []}
    if "outfits" not in meta["wardrobe"] or not isinstance(meta["wardrobe"]["outfits"], list):
        meta["wardrobe"]["outfits"] = []

    # Check for duplicate
    for o in meta["wardrobe"]["outfits"]:
        if o.get("id") == outfit_id:
            print(f"Error: Outfit '{outfit_id}' already registered in {pet_json_path}", file=sys.stderr)
            return 1

    display_name = args.name.strip() if args.name else outfit_id.replace("-", " ").title()
    expected_path = f"outfits/{outfit_id}.webp"

    meta["wardrobe"]["outfits"].append({
        "id": outfit_id,
        "displayName": display_name,
        "spritesheetPath": expected_path
    })

    pet_json_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    
    outfits_dir = DIST_DIR / pet_id / "outfits"
    outfits_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Successfully registered outfit '{display_name}' ({outfit_id}) in {pet_json_path}!")
    print(f"  Expected atlas file: dist/{pet_id}/{expected_path}")
    print(f"  Run 'hatchery package {pet_id}' once the 1536x1872 WebP atlas is placed.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hatchery",
        description="OpenPet Hatchery · Multi-Pet Lifecycle & Wardrobe Management CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="List all managed pets, outfits, and packages")
    p_list.set_defaults(func=cmd_list)

    # new
    p_new = subparsers.add_parser("new", help="Scaffold a new pet specification from template")
    p_new.add_argument("pet_id", help="Lowercase hyphenated pet ID (e.g. 'cyber-cat')")
    p_new.add_argument("--name", help="Display name (defaults to title-cased ID)")
    p_new.add_argument("--category", default="mascots", help="Pet category (default: 'mascots')")
    p_new.add_argument("--desc", help="Short description of the pet")
    p_new.set_defaults(func=cmd_new)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate pet atlases and packages")
    p_val.add_argument("pet_id", nargs="?", help="Optional pet ID to validate (validates all if omitted)")
    p_val.set_defaults(func=cmd_validate)

    # package
    p_pkg = subparsers.add_parser("package", help="Package one or all pets into dist/<pet-id>.zip")
    p_pkg.add_argument("pet_id", nargs="?", help="Optional pet ID to package (packages all if omitted)")
    p_pkg.add_argument("--strip-wardrobe", action="store_true", help="Strip wardrobe from the package")
    p_pkg.set_defaults(func=cmd_package)

    # add-outfit
    p_add = subparsers.add_parser("add-outfit", help="Register a new wardrobe outfit for a pet")
    p_add.add_argument("pet_id", help="Target pet ID")
    p_add.add_argument("outfit_id", help="Lowercase hyphenated outfit ID (e.g. 'cyber-ninja')")
    p_add.add_argument("--name", help="Outfit display name (defaults to title-cased ID)")
    p_add.set_defaults(func=cmd_add_outfit)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

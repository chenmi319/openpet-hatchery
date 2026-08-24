from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

ROOT = Path(__file__).parents[1]


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compose = load_module("compose_atlas", ".opencode/skills/hatch-pet/scripts/compose_atlas.py")
extract = load_module(
    "extract_strip_frames", ".opencode/skills/hatch-pet/scripts/extract_strip_frames.py"
)
inspect_frames = load_module(
    "inspect_frames", ".opencode/skills/hatch-pet/scripts/inspect_frames.py"
)
package = load_module("package_pet", "scripts/package_pet.py")


class PetPipelineTests(unittest.TestCase):
    def test_frame_inspector_warns_for_size_outliers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            frames_root = Path(directory)
            state_dir = frames_root / "test"
            state_dir.mkdir()
            for index, (width, height) in enumerate(
                [(20, 30), (20, 50), (20, 50), (28, 50)]
            ):
                frame = Image.new("RGBA", (192, 208), (0, 0, 0, 0))
                ImageDraw.Draw(frame).rectangle(
                    (50, 50, 50 + width - 1, 50 + height - 1),
                    fill=(40, 120, 220, 255),
                )
                frame.save(state_dir / f"{index:02d}.png")

            args = SimpleNamespace(
                require_components=False,
                allow_stable_slots=False,
                edge_margin=2,
                chroma_adjacent_threshold=150.0,
                min_used_pixels=400,
                edge_pixel_threshold=24,
                chroma_adjacent_pixel_threshold=800,
                small_outlier_ratio=inspect_frames.DEFAULT_SMALL_OUTLIER_RATIO,
                large_outlier_ratio=inspect_frames.DEFAULT_LARGE_OUTLIER_RATIO,
            )
            result = inspect_frames.inspect_state(
                frames_root, "test", 4, {}, None, args
            )

            self.assertTrue(result["ok"])
            self.assertTrue(
                any(
                    "frame 00 is much smaller" in warning
                    for warning in result["warnings"]
                )
            )
            self.assertTrue(
                any(
                    "frame 03 is much larger" in warning
                    for warning in result["warnings"]
                )
            )

    def test_stable_slots_preserve_relative_pose_height(self) -> None:
        strip = Image.new("RGBA", (500, 320), (0, 0, 0, 0))
        draw = ImageDraw.Draw(strip)
        draw.rectangle((40, 10, 139, 309), fill=(40, 120, 220, 255))
        draw.rectangle((340, 70, 439, 309), fill=(40, 120, 220, 255))

        component_frames = extract.extract_component_frames(strip, 2)
        self.assertIsNotNone(component_frames)
        stable_frames = extract.extract_stable_slot_frames(strip, 2)
        assert component_frames is not None

        component_heights = [
            frame.getbbox()[3] - frame.getbbox()[1] for frame in component_frames
        ]
        stable_heights = [
            frame.getbbox()[3] - frame.getbbox()[1] for frame in stable_frames
        ]
        self.assertLessEqual(abs(component_heights[0] - component_heights[1]), 2)
        self.assertGreater(stable_heights[0] - stable_heights[1], 30)

    def test_magenta_spill_removal_preserves_pet_palette(self) -> None:
        image = Image.new("RGBA", (4, 1))
        image.putdata(
            [
                (150, 10, 160, 255),
                (70, 180, 230, 255),
                (230, 150, 90, 255),
                (10, 35, 80, 255),
            ]
        )
        result = extract.remove_chroma_background(image, (255, 0, 255), 96)
        self.assertEqual(result.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(result.getpixel((1, 0)), (70, 180, 230, 255))
        self.assertEqual(result.getpixel((2, 0)), (230, 150, 90, 255))
        self.assertEqual(result.getpixel((3, 0)), (10, 35, 80, 255))

    def test_pixel_grid_produces_identical_two_by_two_blocks(self) -> None:
        atlas = Image.new("RGBA", (compose.ATLAS_WIDTH, compose.ATLAS_HEIGHT), (0, 0, 0, 0))
        atlas.putpixel((1, 1), (255, 0, 0, 255))
        result = compose.apply_pixel_grid(atlas, 2)
        block = {result.getpixel((x, y)) for x in range(2) for y in range(2)}
        self.assertEqual(len(block), 1)

    def test_package_has_only_root_runtime_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pet_dir = root / "goat-leo"
            pet_dir.mkdir()
            (pet_dir / "pet.json").write_text(
                json.dumps(
                    {
                        "id": "goat-leo",
                        "displayName": "GOAT Leo",
                        "description": "test",
                        "spritesheetPath": "spritesheet.webp",
                    }
                ),
                encoding="utf-8",
            )
            Image.new("RGBA", package.ATLAS_SIZE, (0, 0, 0, 0)).save(
                pet_dir / "spritesheet.webp", format="WEBP", lossless=True
            )
            output = root / "goat-leo.zip"
            package.package_pet(pet_dir, output)

            import zipfile

            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), package.REQUIRED_FILES)

    def test_full_atlas_compose_and_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames = root / "frames"
            for state, _row, frame_count in compose.ROW_SPECS:
                state_dir = frames / state
                state_dir.mkdir(parents=True)
                for index in range(frame_count):
                    frame = Image.new("RGBA", (192, 208), (0, 0, 0, 0))
                    for y in range(80, 160):
                        for x in range(64 + index % 2 * 2, 128 + index % 2 * 2):
                            frame.putpixel((x, y), (40, 120, 220, 255))
                    frame.save(state_dir / f"{index:02d}.png")

            png = root / "spritesheet.png"
            webp = root / "spritesheet.webp"
            validation = root / "validation.json"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / ".opencode/skills/hatch-pet/scripts/compose_atlas.py"),
                    "--frames-root",
                    str(frames),
                    "--output",
                    str(png),
                    "--webp-output",
                    str(webp),
                    "--pixel-grid-scale",
                    "2",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / ".opencode/skills/hatch-pet/scripts/validate_atlas.py"),
                    str(webp),
                    "--json-out",
                    str(validation),
                    "--pixel-grid-scale",
                    "2",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(validation.read_text(encoding="utf-8"))
            self.assertTrue(report["ok"])
            self.assertEqual(report["pixel_grid_violations"], 0)


if __name__ == "__main__":
    unittest.main()

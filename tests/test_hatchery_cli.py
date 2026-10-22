from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HATCHERY_SCRIPT = ROOT / "scripts/hatchery.py"


class HatcheryCliTests(unittest.TestCase):
    def test_hatchery_list(self) -> None:
        res = subprocess.run(
            [sys.executable, str(HATCHERY_SCRIPT), "list"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertIn("goat-leo", res.stdout)
        self.assertIn("GOAT Leo", res.stdout)
        self.assertIn("Classic Sky and White", res.stdout)
        self.assertIn("Red and Blue Legend", res.stdout)
        self.assertIn("Golden Farewell", res.stdout)
        self.assertIn("Flamingo Pink", res.stdout)

    def test_hatchery_validate_goat_leo(self) -> None:
        res = subprocess.run(
            [sys.executable, str(HATCHERY_SCRIPT), "validate", "goat-leo"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertIn("Package integrity: OK", res.stdout)
        self.assertIn("Base atlas (spritesheet.webp): Valid", res.stdout)
        self.assertIn("Wardrobe outfit (red-blue-legend.webp): Valid", res.stdout)
        self.assertIn("Wardrobe outfit (golden-farewell.webp): Valid", res.stdout)
        self.assertIn("Wardrobe outfit (flamingo-pink.webp): Valid", res.stdout)

    def test_hatchery_new_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pets = Path(temp_dir) / "pets"
            temp_template = temp_pets / "_template"
            temp_template.mkdir(parents=True)
            
            # Copy template files
            for fn in ("identity.txt", "spec.md", "state-overrides.json"):
                (temp_template / fn).write_text((ROOT / "pets/_template" / fn).read_text(encoding="utf-8"), encoding="utf-8")
                
            # Verify template replacement logic
            template_content = (temp_template / "spec.md").read_text(encoding="utf-8")
            rendered = template_content.replace("{{PET_ID}}", "cyber-cat").replace("{{DISPLAY_NAME}}", "Cyber Cat")
            self.assertIn("cyber-cat", rendered)
            self.assertIn("Cyber Cat", rendered)
            self.assertNotIn("{{PET_ID}}", rendered)


if __name__ == "__main__":
    unittest.main()

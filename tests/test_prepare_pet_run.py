from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / ".opencode/skills/hatch-pet/scripts/prepare_pet_run.py"


class PreparePetRunTests(unittest.TestCase):
    def test_state_overrides_and_no_mirror_are_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--pet-name",
                    "GOAT Leo",
                    "--pet-id",
                    "goat-leo",
                    "--pet-notes",
                    "fixed dark number 10",
                    "--state-overrides-file",
                    str(ROOT / "pets/goat-leo/state-overrides.json"),
                    "--forbid-running-left-mirror",
                    "--output-dir",
                    str(run_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            jobs = json.loads((run_dir / "imagegen-jobs.json").read_text(encoding="utf-8"))
            running_left = next(job for job in jobs["jobs"] if job["id"] == "running-left")
            self.assertFalse(running_left["derivation_policy"]["may_derive"])
            prompt = (run_dir / "prompts/rows/running-left.md").read_text(encoding="utf-8")
            self.assertIn("never mirror the rightward row", prompt)
            self.assertIn("no scenery, unapproved text", prompt)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / ".opencode/skills/hatch-pet/scripts/prepare_pet_run.py"


class PreparePetRunTests(unittest.TestCase):
    def test_running_and_celebration_overrides_do_not_conflict(self) -> None:
        spec = importlib.util.spec_from_file_location("prepare_pet_run", SCRIPT)
        assert spec and spec.loader
        prepare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prepare)
        from types import SimpleNamespace

        args = SimpleNamespace(
            pet_id="goat-leo", pet_notes="fixed number 10; near ball may briefly leave the boot",
            style_preset="pixel", style_notes="full resolution",
            chroma_key={"hex": "#FF00FF", "name": "magenta"},
            state_overrides={"running": "continuous sprint", "review": "dribbling run", "jumping": "continuous sky-point running celebration"},
        )
        for state in args.state_overrides:
            for builder in (prepare.row_prompt, prepare.retry_row_prompt):
                prompt = builder(args, state, 7, 6, "")
                self.assertIn(args.state_overrides[state], prompt)
                self.assertNotIn("not literal foot-running", prompt)
                self.assertNotIn("Do not show literal foot-running", prompt)
                self.assertNotIn("anticipation, lift, airborne peak, descent, settle", prompt)
                self.assertIn("scenery", prompt)

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

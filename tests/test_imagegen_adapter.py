from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import httpx

SCRIPT = Path(__file__).parents[1] / ".opencode/skills/imagegen/scripts/image_gen.py"
SPEC = importlib.util.spec_from_file_location("image_gen", SCRIPT)
assert SPEC and SPEC.loader
image_gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(image_gen)


class ImagegenAdapterTests(unittest.TestCase):
    def test_dry_run_allows_missing_runtime_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            image_gen, "DEFAULT_RUNTIME_CONFIG_PATH", Path(directory) / "missing.json"
        ):
            self.assertIsNone(image_gen._runtime_config(True))

    def test_live_call_requires_local_runtime_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            image_gen, "DEFAULT_RUNTIME_CONFIG_PATH", Path(directory) / "missing.json"
        ):
            with self.assertRaises(SystemExit):
                image_gen._runtime_config(False)

    def test_local_runtime_file_resolves_separate_key_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key_file = root / "key"
            key_file.write_text("secret", encoding="utf-8")
            runtime_file = root / ".imagegen.local.json"
            runtime_file.write_text(
                json.dumps({"baseUrl": "https://example.com/v1", "apiKeyFile": str(key_file)}),
                encoding="utf-8",
            )
            with mock.patch.object(image_gen, "DEFAULT_RUNTIME_CONFIG_PATH", runtime_file):
                self.assertEqual(image_gen._runtime_config(False), ("https://example.com/v1", key_file))

    def test_call_ledger_enforces_hard_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "calls.json"
            image_gen._reserve_call(str(ledger), 1, "generate", "gpt-image-2")
            saved = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual(saved["calls"][0]["operation"], "generate")
            with self.assertRaises(SystemExit):
                image_gen._reserve_call(str(ledger), 1, "edit", "gpt-image-2")

    def test_private_image_url_is_rejected_before_download(self) -> None:
        with self.assertRaises(SystemExit):
            image_gen._download_image("https://127.0.0.1/image.png")

    def test_public_url_response_is_downloaded_as_binary(self) -> None:
        png = b"\x89PNG\r\n\x1a\n" + b"payload"

        class Response:
            is_redirect = False
            headers = {"content-length": str(len(png))}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def raise_for_status(self) -> None:
                return None

            def iter_bytes(self):
                yield png

        with mock.patch.object(httpx, "stream", return_value=Response()):
            self.assertEqual(image_gen._download_image("https://example.com/image.png"), png)


if __name__ == "__main__":
    unittest.main()

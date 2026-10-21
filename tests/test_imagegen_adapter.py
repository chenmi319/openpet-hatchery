from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import httpx
import openai

SCRIPT = Path(__file__).parents[1] / ".opencode/skills/imagegen/scripts/image_gen.py"
SPEC = importlib.util.spec_from_file_location("image_gen", SCRIPT)
assert SPEC and SPEC.loader
image_gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(image_gen)


class ImagegenAdapterTests(unittest.TestCase):
    def test_nano_model_and_option_boundaries(self) -> None:
        payload = {"model": "Nano Banana 2.1", "quality": "auto", "prompt": "test", "n": 1}
        image_gen._validate_model(payload["model"])
        image_gen._validate_nano_options(payload, image_count=14)
        for override in ({"quality": "high"}, {"background": "transparent"}, {"output_format": "png"},
                         {"input_fidelity": "high"}, {"moderation": "low"}, {"output_compression": 90},
                         {"n": 2}, {"prompt": "x" * 4001}):
            with self.subTest(override=override), self.assertRaises(SystemExit):
                image_gen._validate_nano_options({**payload, **override})
        for options in ({"mask": True}, {"image_count": 15}):
            with self.assertRaises(SystemExit):
                image_gen._validate_nano_options(payload, **options)
        with self.assertRaises(SystemExit):
            image_gen._validate_model("Nano Banana Pro")
        image_gen._validate_nano_options({"model": "gpt-image-2", "quality": "high", "background": "transparent"})

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

    def test_call_ledger_counts_beyond_legacy_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "calls.json"
            image_gen._reserve_call(str(ledger), 1, "generate", "gpt-image-2")
            saved = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual(saved["calls"][0]["operation"], "generate")
            ledger.write_text(json.dumps({"schemaVersion": 1, "maxCalls": 100, "calls": saved["calls"] * 100}))
            image_gen._reserve_call(str(ledger), 1, "edit", "gpt-image-2")
            saved = json.loads(ledger.read_text())
            self.assertEqual(len(saved["calls"]), 101)
            self.assertEqual(saved["calls"][-1]["number"], 101)
            self.assertNotIn("maxCalls", saved)

    def test_call_ledger_rejects_invalid_shape_and_requires_path(self) -> None:
        with self.assertRaises(SystemExit):
            image_gen._reserve_call(None, None, "edit", "gpt-image-2")
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "calls.json"
            for value in ([], {"calls": "invalid"}):
                ledger.write_text(json.dumps(value))
                with self.assertRaises(SystemExit):
                    image_gen._reserve_call(str(ledger), None, "edit", "gpt-image-2")

    def test_paid_request_is_not_automatically_retried(self) -> None:
        requests = []

        def fail(request):
            requests.append(request.method)
            return httpx.Response(503, json={"error": {"message": "test failure"}})

        with mock.patch.object(
            image_gen, "_runtime_config", return_value=("https://example.com/v1", Path("unused"))
        ), mock.patch.object(image_gen, "_read_api_key", return_value="test-only"):
            with image_gen._create_client() as base_client, httpx.Client(
                transport=httpx.MockTransport(fail)
            ) as transport:
                client = base_client.with_options(http_client=transport)
                with self.assertRaises(openai.InternalServerError):
                    client.images.edit(model="gpt-image-2", prompt="test", image=b"test-image")

        self.assertEqual(requests, ["POST"])

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

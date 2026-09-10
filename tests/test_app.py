"""Offline regressions: real NumPy, mocked UI and model dependencies."""
import base64
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

import numpy as np


def load_app():
    gradio = MagicMock()
    gradio.Error = type("GradioError", (Exception,), {})
    gradio.update.side_effect = lambda **kwargs: kwargs
    spaces = types.SimpleNamespace(GPU=lambda fn=None, **kwargs: fn or (lambda f: f))
    data_types = types.SimpleNamespace(
        ChatMLSample=lambda **kw: types.SimpleNamespace(**kw),
        Message=lambda **kw: types.SimpleNamespace(**kw),
        AudioContent=lambda **kw: types.SimpleNamespace(**kw),
    )
    modules = {
        "gradio": gradio, "spaces": spaces, "torch": MagicMock(),
        "loguru": MagicMock(), "higgs_audio": MagicMock(),
        "higgs_audio.serve": MagicMock(),
        "higgs_audio.serve.serve_engine": MagicMock(),
        "higgs_audio.data_types": data_types,
    }
    spec = importlib.util.spec_from_file_location("higgs_app", Path(__file__).parents[1] / "app.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


app = load_app()


class AppTests(unittest.TestCase):
    def setUp(self):
        app.engine = None
        app.VOICE_PRESETS = {"EMPTY": "No reference voice"}

    def test_blank_text_does_not_load_model(self):
        for text in (None, "", " \n ", "( )"):
            with patch.object(app, "initialize_engine") as initialize:
                with self.assertRaises(app.gr.Error):
                    app.text_to_speech(text, "EMPTY")
                initialize.assert_not_called()

    def test_reference_file_is_not_stale(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "voice.wav"
            path.write_bytes(b"first")
            app.encode_audio_file(path)
            path.write_bytes(b"second")
            self.assertEqual(base64.b64decode(app.encode_audio_file(path)), b"second")

    def test_stop_payloads(self):
        for value in ({"data": [[" stop "], [], [None], [float("nan")]]},
                      {"stops": "stop"}, [["stop"], []], [" stop "]):
            self.assertEqual(app.extract_stop_strings(value), ["stop"])
        self.assertEqual(app.extract_stop_strings([[None], []]), app.DEFAULT_STOP_STRINGS)

    def test_audio_clips_instead_of_wrapping(self):
        result = app.check_return_audio(np.array([-2., -1., 0., 1., 2.]))
        np.testing.assert_array_equal(result, [-32767, -32767, 0, 32767, 32767])
        self.assertEqual(result.dtype, np.int16)
        self.assertIsNone(app.check_return_audio(np.zeros(4)))
        for value in ([], [np.nan], [np.inf]):
            with self.assertRaises(ValueError):
                app.check_return_audio(np.array(value))

    def test_preset_validation_and_missing_audio(self):
        with self.assertRaises(ValueError):
            app.get_voice_preset("../../secret")
        for name in ("../secret.wav", "..\\secret.wav"):
            with self.assertRaises(ValueError):
                app._download_voice_preset_file(name)
        with patch.object(app, "get_voice_preset", return_value=(None, "")):
            with self.assertRaises(ValueError):
                app.prepare_chatml_sample("missing", "Hello")

    def test_nullable_system_prompt(self):
        sample = app.prepare_chatml_sample("EMPTY", "Hello", system_prompt=None)
        self.assertEqual(len(sample.messages), 1)
        self.assertEqual(sample.messages[0].content, "Hello.")

    def test_generation_errors_are_api_errors(self):
        app.engine = MagicMock()
        app.engine.generate.side_effect = RuntimeError("model failed")
        with self.assertRaisesRegex(app.gr.Error, "model failed"):
            app.text_to_speech("Hello", "EMPTY")

    def test_successful_generation(self):
        app.engine = MagicMock()
        app.engine.generate.return_value = types.SimpleNamespace(
            generated_text="<|AUDIO_OUT|><|AUDIO_OUT|>",
            audio=np.array([0.5, -0.5]), sampling_rate=24000,
        )
        text, audio = app.text_to_speech("Hello", "EMPTY", top_k=0, ras_win_len=0)
        self.assertEqual(text, "<|AUDIO_OUT|>")
        self.assertEqual(audio[0], 24000)
        self.assertIsNone(app.engine.generate.call_args.kwargs["top_k"])

    def test_template_clears_hidden_reference_and_handles_offline_presets(self):
        app.create_ui()
        event = app.gr.Dropdown.return_value.change.call_args.kwargs
        callback = event["fn"]
        clone = callback("voice-clone")
        self.assertEqual(clone[3]["value"], "EMPTY")
        ordinary = callback("smart-voice")
        self.assertEqual(ordinary[-2:], (None, ""))
        self.assertEqual(len(ordinary), len(event["outputs"]))
        self.assertEqual(len(callback("unknown")), len(event["outputs"]))


if __name__ == "__main__":
    unittest.main()

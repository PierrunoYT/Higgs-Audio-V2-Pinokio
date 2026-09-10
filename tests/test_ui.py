"""Construct the real Gradio UI without downloading model weights."""
import os
import unittest
from unittest.mock import patch

from test_app import load_app

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
try:
    import gradio
except ImportError:
    gradio = None


@unittest.skipIf(gradio is None, "Install Gradio to run the UI smoke test")
class UITests(unittest.TestCase):
    def test_build_and_api_schema(self):
        app = load_app()
        with patch.object(app, "gr", gradio):
            demo, _, _ = app.create_ui()
            api = demo.get_api_info()
        self.assertIn("/generate_speech", api["named_endpoints"])
        self.assertEqual(len(api["named_endpoints"]["/generate_speech"]["parameters"]), 12)
        demo.close()


if __name__ == "__main__":
    unittest.main()

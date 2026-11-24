"""Construct the real Gradio UI without downloading model weights."""
import asyncio
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
        # Outside a running loop, Gradio creates event loops it never closes; their finalizer
        # warnings can fire mid-import and corrupt the import lock on Python 3.10.
        async def build():
            return app.create_ui()

        with patch.object(app, "gr", gradio):
            demo, _, _ = asyncio.run(build())
            api = demo.get_api_info()
        self.assertIn("/generate_speech", api["named_endpoints"])
        self.assertEqual(len(api["named_endpoints"]["/generate_speech"]["parameters"]), 12)
        demo.close()


if __name__ == "__main__":
    unittest.main()

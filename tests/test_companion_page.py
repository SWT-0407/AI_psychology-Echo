import sys
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class CompanionPageInputTests(unittest.TestCase):
    def test_message_box_clears_after_send(self):
        script = """
import streamlit as st
from ui import companion_page as cp


class DummyMultimodalManager:
    def listen_speech(self, timeout=5.0):
        return ""


def fake_submit(selected, prompt, emotion=None, image=None):
    st.session_state["sent_prompt"] = prompt
    st.rerun()


cp._submit_companion_message = fake_submit
cp._uploaded_image_message = lambda uploaded_file: None
cp._audio_to_text = lambda scope, audio_file: ""
cp.get_multimodal_manager = lambda: DummyMultimodalManager()
cp._render_message_form({"id": "abc"})
"""
        app = AppTest.from_string(script)

        app.run(timeout=5)
        app.text_area(key="companion_text_abc").input("hello").run(timeout=5)

        self.assertEqual(app.text_area(key="companion_text_abc").value, "hello")

        app.button(key="companion_send_arrow").click().run(timeout=5)

        self.assertEqual(app.session_state["sent_prompt"], "hello")
        self.assertEqual(app.text_area(key="companion_text_abc").value, "")


if __name__ == "__main__":
    unittest.main()

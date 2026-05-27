import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.message_format import compact_session_record, hydrate_session_record
from services import storage_local


class StorageLightweightTests(unittest.TestCase):
    def test_compact_record_drops_duplicate_fields_but_hydrates_them(self):
        record = {
            "session_id": "s1",
            "title": "check",
            "display_messages": [{"role": "user", "content": "hello"}],
            "messages": [{"role": "user", "content": "hello"}],
            "conversation_text": "duplicate",
            "diary_profile": {"name": "demo"},
            "diary_moods": {"2026-05-27": "ok"},
            "user_profile_summary": {"level": "ok"},
        }

        compact = compact_session_record(record)
        self.assertNotIn("display_messages", compact)
        self.assertNotIn("conversation_text", compact)
        self.assertNotIn("diary_profile", compact)
        self.assertEqual(compact["storage_version"], "diary_v3_compact")

        hydrated = hydrate_session_record(compact)
        self.assertIn("messages", hydrated)
        self.assertIn("display_messages", hydrated)
        self.assertIn("conversation_text", hydrated)

    def test_storage_local_writes_compact_and_loads_compatible_shape(self):
        old_history_dir = storage_local.HISTORY_DIR
        old_scores_dir = storage_local.SCORES_DIR

        try:
            with tempfile.TemporaryDirectory() as tmp:
                storage_local.HISTORY_DIR = tmp
                storage_local.SCORES_DIR = tmp
                storage_local.save_complete_session(
                    "light_test",
                    {
                        "session_id": "light_test",
                        "display_messages": [{"role": "user", "content": "hello"}],
                        "messages": [{"role": "user", "content": "hello"}],
                        "conversation_text": "duplicate",
                        "scores": {},
                    },
                )

                raw = Path(tmp, "light_test.json").read_text(encoding="utf-8")
                stored = json.loads(raw)
                self.assertIn("messages", stored)
                self.assertNotIn("display_messages", stored)
                self.assertNotIn("conversation_text", stored)

                loaded = storage_local.load_session("light_test")
                self.assertIn("display_messages", loaded)
                self.assertIn("conversation_text", loaded)
        finally:
            storage_local.HISTORY_DIR = old_history_dir
            storage_local.SCORES_DIR = old_scores_dir


if __name__ == "__main__":
    unittest.main()

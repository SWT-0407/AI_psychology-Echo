import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import storage_cloud, storage_local


class FakeResult:
    def __init__(self, data=None, count=None):
        self.data = data if data is not None else []
        self.count = count


class FakeTable:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.action = None

    def select(self, *args, **kwargs):
        self.action = "select"
        self.client.calls.append(("select", self.name, args, kwargs))
        return self

    def upsert(self, record, **kwargs):
        self.action = "upsert"
        self.client.calls.append(("upsert", self.name, record, kwargs))
        return self

    def update(self, record):
        self.action = "update"
        self.client.calls.append(("update", self.name, record))
        return self

    def eq(self, field, value):
        self.client.calls.append(("eq", field, value))
        return self

    def order(self, field, **kwargs):
        self.client.calls.append(("order", field, kwargs))
        return self

    def execute(self):
        self.client.calls.append(("execute", self.action))
        if self.action == "select":
            return FakeResult(self.client.records)
        if self.action == "upsert" and self.client.fail_upsert_with_duplicate:
            raise Exception(
                "{'message': 'duplicate key value violates unique constraint "
                "\"chat_history_session_id_key\"', 'code': '23505'}"
            )
        return FakeResult()


class FakeClient:
    def __init__(self, fail_upsert_with_duplicate=False, records=None):
        self.fail_upsert_with_duplicate = fail_upsert_with_duplicate
        self.records = records or []
        self.calls = []

    def table(self, name):
        return FakeTable(self, name)


class StorageCloudTests(unittest.TestCase):
    def setUp(self):
        self.old_get_client = storage_cloud._get_client
        self.old_marker_file = storage_cloud.SYNC_MARKER_FILE
        self.old_st = storage_cloud.st
        self.old_history_dir = storage_local.HISTORY_DIR
        self.old_scores_dir = storage_local.SCORES_DIR
        self.tmpdir = tempfile.TemporaryDirectory()
        storage_cloud.SYNC_MARKER_FILE = str(Path(self.tmpdir.name, "synced.txt"))
        storage_local.HISTORY_DIR = str(Path(self.tmpdir.name, "history"))
        storage_local.SCORES_DIR = str(Path(self.tmpdir.name, "scores"))
        self.errors = []
        storage_cloud.st = SimpleNamespace(
            session_state={"user_id": "user_1"},
            error=self.errors.append,
        )

    def tearDown(self):
        storage_cloud._get_client = self.old_get_client
        storage_cloud.SYNC_MARKER_FILE = self.old_marker_file
        storage_cloud.st = self.old_st
        storage_local.HISTORY_DIR = self.old_history_dir
        storage_local.SCORES_DIR = self.old_scores_dir
        self.tmpdir.cleanup()

    def test_upload_upserts_on_session_id_and_marks_success_without_returned_rows(self):
        client = FakeClient()
        storage_cloud._get_client = lambda: client

        ok = storage_cloud.upload_session_to_cloud(
            "session_1",
            {"messages": [{"role": "user", "content": "hello"}]},
            upload_full_content=True,
        )

        self.assertTrue(ok)
        self.assertEqual(self.errors, [])
        upsert_calls = [call for call in client.calls if call[0] == "upsert"]
        self.assertEqual(upsert_calls[0][3], {"on_conflict": "session_id"})
        self.assertIn("session_1", Path(storage_cloud.SYNC_MARKER_FILE).read_text(encoding="utf-8"))

    def test_duplicate_session_id_falls_back_to_update(self):
        client = FakeClient(fail_upsert_with_duplicate=True)
        storage_cloud._get_client = lambda: client

        ok = storage_cloud.upload_session_to_cloud("session_2", {"messages": []})

        self.assertTrue(ok)
        self.assertEqual(self.errors, [])
        self.assertIn(("execute", "upsert"), client.calls)
        self.assertTrue(any(call[0] == "update" for call in client.calls))
        self.assertIn(("eq", "session_id", "session_2"), client.calls)

    def test_sync_cloud_to_local_persists_fetched_records(self):
        client = FakeClient(
            records=[
                {
                    "session_id": "cloud_1",
                    "user_id": "user_1",
                    "timestamp": "2026-05-27T12:00:00",
                    "display_messages": [{"role": "user", "content": "hello from cloud"}],
                    "scores": {"x1": 8},
                    "summary": "from cloud",
                }
            ]
        )
        storage_cloud._get_client = lambda: client

        saved = storage_cloud.sync_cloud_to_local("user_1")

        self.assertEqual(saved, 1)
        self.assertIn(("eq", "user_id", "user_1"), client.calls)
        loaded = storage_local.load_session("cloud_1")
        self.assertEqual(loaded["messages"][0]["content"], "hello from cloud")
        self.assertEqual(loaded["summary"], "from cloud")
        self.assertIn("cloud_1", Path(storage_cloud.SYNC_MARKER_FILE).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import storage_cloud


class FakeResult:
    data = []


class FakeTable:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.action = None

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

    def execute(self):
        self.client.calls.append(("execute", self.action))
        if self.action == "upsert" and self.client.fail_upsert_with_duplicate:
            raise Exception(
                "{'message': 'duplicate key value violates unique constraint "
                "\"chat_history_session_id_key\"', 'code': '23505'}"
            )
        return FakeResult()


class FakeClient:
    def __init__(self, fail_upsert_with_duplicate=False):
        self.fail_upsert_with_duplicate = fail_upsert_with_duplicate
        self.calls = []

    def table(self, name):
        return FakeTable(self, name)


class StorageCloudTests(unittest.TestCase):
    def setUp(self):
        self.old_get_client = storage_cloud._get_client
        self.old_marker_file = storage_cloud.SYNC_MARKER_FILE
        self.old_st = storage_cloud.st
        self.tmpdir = tempfile.TemporaryDirectory()
        storage_cloud.SYNC_MARKER_FILE = str(Path(self.tmpdir.name, "synced.txt"))
        self.errors = []
        storage_cloud.st = SimpleNamespace(
            session_state={"user_id": "user_1"},
            error=self.errors.append,
        )

    def tearDown(self):
        storage_cloud._get_client = self.old_get_client
        storage_cloud.SYNC_MARKER_FILE = self.old_marker_file
        storage_cloud.st = self.old_st
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


if __name__ == "__main__":
    unittest.main()

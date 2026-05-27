import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.local_ai import generate_reply, score_messages


class LocalAiDialogueTests(unittest.TestCase):
    def test_score_messages_tracks_dimension_specific_distress(self):
        text = "\u6211\u6700\u8fd1\u5931\u7720\uff0c\u7126\u8651\uff0c\u5b66\u4e0d\u8fdb\u53bb\uff0c\u8fd8\u89c9\u5f97\u6ca1\u4eba\u61c2\u6211\uff0c\u5f88\u8ff7\u832b"
        scores = score_messages([{"role": "user", "content": text}])

        self.assertLessEqual(scores["x4"], 4)
        self.assertLessEqual(scores["x5"], 4)
        self.assertLess(scores["x6"], 6)

    def test_score_messages_keeps_positive_resources_visible(self):
        text = "\u4eca\u5929\u5f88\u5f00\u5fc3\uff0c\u5b66\u4e60\u8ba1\u5212\u5b8c\u6210\u4e86\uff0c\u4e5f\u548c\u670b\u53cb\u804a\u4e86\u804a\uff0c\u611f\u89c9\u6709\u5e0c\u671b"
        scores = score_messages([{"role": "user", "content": text}])

        self.assertGreaterEqual(scores["x1"], 8)
        self.assertGreaterEqual(scores["x4"], 8)
        self.assertGreaterEqual(scores["x5"], 7)

    def test_psytest_reply_asks_one_targeted_followup(self):
        text = "\u6211\u6700\u8fd1\u5931\u7720\uff0c\u7126\u8651\uff0c\u5b66\u4e0d\u8fdb\u53bb"
        messages = [{"role": "user", "content": text}]
        scores = score_messages(messages)
        reply = generate_reply("psytest", text, messages, scores)

        self.assertIn("\u53ea\u8865\u4e00\u4e2a\u5173\u952e\u7ebf\u7d22", reply)
        self.assertLessEqual(reply.count("\uff1f"), 2)


if __name__ == "__main__":
    unittest.main()

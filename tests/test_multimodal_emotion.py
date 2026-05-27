import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.multimodal_service import EmotionDetector


class MultimodalEmotionTests(unittest.TestCase):
    def test_api_error_is_not_displayed_as_calm(self):
        detector = EmotionDetector()

        detector._apply_smoothed_result({
            "emotion": "unknown",
            "status": "api_error",
            "confidence": 0.0,
            "analysis": "服务异常",
            "error": "boom",
        })

        state = detector.get_emotion()
        self.assertEqual(state["emotion"], "unknown")
        self.assertEqual(state["status"], "api_error")
        self.assertNotIn("平静", state["emotion_cn"])

    def test_recent_non_neutral_result_can_override_old_neutral_votes(self):
        detector = EmotionDetector()
        neutral = {
            "emotion": "neutral",
            "status": "ok",
            "confidence": 0.8,
            "valence": 0.5,
            "arousal": 0.3,
            "dominance": 0.5,
            "anxiety": 0.0,
            "fatigue": 0.0,
            "engagement": 0.5,
        }
        anxious = {
            "emotion": "anxious",
            "status": "ok",
            "confidence": 0.48,
            "valence": 0.35,
            "arousal": 0.7,
            "dominance": 0.35,
            "anxiety": 0.68,
            "fatigue": 0.2,
            "engagement": 0.4,
            "analysis": "眉眼紧张",
        }

        detector._apply_smoothed_result(neutral)
        detector._apply_smoothed_result(neutral)
        detector._apply_smoothed_result(anxious)

        state = detector.get_emotion()
        self.assertEqual(state["emotion"], "anxious")
        self.assertEqual(state["status"], "ok")
        self.assertIn("焦虑", state["emotion_cn"])


if __name__ == "__main__":
    unittest.main()

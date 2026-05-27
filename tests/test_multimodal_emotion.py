import sys
import unittest
from pathlib import Path

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.multimodal_service import EmotionDetector
from services.ai_service import _normalize_face_emotion
from Multimodal.config import EMOTION_ANALYSIS_PROMPT, build_face_label_description, build_face_scale_description


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

    def test_fine_grained_emotion_aliases_are_normalized(self):
        self.assertEqual(_normalize_face_emotion("worried"), "anxious")
        self.assertEqual(_normalize_face_emotion("tense"), "stressed")
        self.assertEqual(_normalize_face_emotion("sleepy"), "tired")

    def test_detector_displays_new_fine_grained_labels(self):
        detector = EmotionDetector()

        detector._apply_smoothed_result({
            "emotion": "confused",
            "status": "ok",
            "confidence": 0.73,
            "valence": 0.42,
            "arousal": 0.56,
            "dominance": 0.45,
            "anxiety": 0.22,
            "fatigue": 0.08,
            "engagement": 0.68,
            "analysis": "眉头疑惑",
        })

        state = detector.get_emotion()
        self.assertEqual(state["emotion"], "confused")
        self.assertIn("困惑", state["emotion_cn"])

    def test_prompt_contains_fine_grained_label_descriptions(self):
        prompt = EMOTION_ANALYSIS_PROMPT.format(
            face_scale_desc=build_face_scale_description(),
            face_label_desc=build_face_label_description(),
        )

        self.assertIn("stressed（压力大）", prompt)
        self.assertIn("embarrassed（尴尬）", prompt)
        self.assertIn("withdrawn（回避）", prompt)

    def test_preview_frame_keeps_target_screen_ratio(self):
        detector = EmotionDetector(preview_enabled=False)
        frame = np.full((480, 640, 3), 255, dtype=np.uint8)

        preview = detector._fit_frame_to_preview(frame, 400, 225)

        self.assertEqual(preview.shape, (225, 400, 3))
        self.assertTrue((preview[:, :40] == 18).all())
        self.assertTrue((preview[:, 350:] == 18).all())
        self.assertTrue((preview[:, 50:340] == 255).any())


if __name__ == "__main__":
    unittest.main()

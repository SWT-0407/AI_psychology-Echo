import unittest
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.safety import assess_message_safety


class SafetyAssessmentTests(unittest.TestCase):
    def test_self_harm_language_triggers_crisis(self):
        assessment = assess_message_safety("我想自杀，已经准备好了")

        self.assertEqual(assessment.level, "crisis")
        self.assertIn("自杀", assessment.matched_terms)

    def test_harm_others_language_triggers_crisis(self):
        assessment = assess_message_safety("我怕自己会伤害别人")

        self.assertEqual(assessment.level, "crisis")
        self.assertIn("伤害别人", assessment.matched_terms)

    def test_distress_language_needs_support_without_crisis_popup(self):
        assessment = assess_message_safety("我真的撑不住了，好累")

        self.assertEqual(assessment.level, "distress")
        self.assertFalse(assessment.is_crisis)
        self.assertTrue(assessment.needs_support)

    def test_clear_negation_does_not_trigger_crisis(self):
        assessment = assess_message_safety("我不是想死，只是今天很难过")

        self.assertEqual(assessment.level, "none")


if __name__ == "__main__":
    unittest.main()

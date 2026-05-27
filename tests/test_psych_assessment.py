import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.psych_assessment import build_integrated_assessment, format_assessment_markdown, score_dimensions


class PsychAssessmentScoreDirectionTests(unittest.TestCase):
    def test_dimension_score_keeps_higher_as_healthier(self):
        dimensions = score_dimensions(
            {"x1": 8, "x2": 7, "x3": 6, "x4": 5, "x5": 4, "x6": 3},
            [{"role": "user", "content": ""}],
        )

        self.assertEqual(dimensions["x1"]["score"], 80.0)
        self.assertEqual(dimensions["x6"]["score"], 30.0)
        self.assertGreater(dimensions["x1"]["score"], dimensions["x6"]["score"])

    def test_distress_evidence_reduces_health_score(self):
        baseline = score_dimensions({"x2": 7}, [{"role": "user", "content": ""}])
        distressed = score_dimensions(
            {"x2": 7},
            [{"role": "user", "content": "我最近焦虑紧张，压力很大，感觉喘不过气。"}],
        )

        self.assertLess(distressed["x2"]["score"], baseline["x2"]["score"])
        self.assertGreater(distressed["x2"]["concern_score"], baseline["x2"]["concern_score"])

    def test_report_describes_health_scores(self):
        assessment = build_integrated_assessment(
            {"x1": 6, "x2": 6, "x3": 6, "x4": 6, "x5": 6, "x6": 6},
            [{"role": "user", "content": "最近有一点压力，但还能正常学习。"}],
        )
        markdown = format_assessment_markdown(assessment)

        self.assertIn("健康分", markdown)
        self.assertNotIn("困扰分", markdown)
        self.assertNotIn("功能受损", markdown)
        self.assertNotIn("风险保护", markdown)
        self.assertNotIn("风险因素", markdown)
        self.assertNotIn("保护因素", markdown)
        self.assertEqual(assessment["score_direction"], "six_dimensions.score 为 0-100 健康分，分数越高代表心理状态越稳定")

    def test_crisis_gate_remains_backend_only_in_user_report(self):
        assessment = build_integrated_assessment(
            {"x1": 4, "x2": 4, "x3": 4, "x4": 4, "x5": 4, "x6": 4},
            [{"role": "user", "content": "我想自杀，已经准备了药。"}],
        )
        markdown = format_assessment_markdown(assessment)

        self.assertEqual(assessment["risk_protection_gate"]["level"], "R3")
        self.assertIn("专业人士", markdown)
        self.assertNotIn("风险保护", markdown)
        self.assertNotIn("风险因素", markdown)
        self.assertNotIn("保护因素", markdown)
        self.assertNotIn("R3", markdown)


if __name__ == "__main__":
    unittest.main()

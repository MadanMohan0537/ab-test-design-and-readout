import unittest

from backend.app.design import generate_design, validate_design
from backend.app.models import ExperimentDesign, MetricDefinition


def design(**overrides):
    values = dict(
        hypothesis="Social proof increases conversion", control="Current page", treatment="Social-proof page",
        primary_metric=MetricDefinition("conversion"), guardrail_metrics=(MetricDefinition("support", "decrease"),),
        baseline_rate=.08, expected_relative_lift=.05, daily_eligible_users=12000, minimum_days=14,
    )
    values.update(overrides)
    return ExperimentDesign(**values)


class DesignTests(unittest.TestCase):
    def test_generates_complete_fixed_horizon_design(self):
        result = generate_design(design())
        self.assertEqual(result["sample_size"]["per_arm"], 73853)
        self.assertEqual(result["sample_size"]["total"], 147706)
        self.assertEqual(result["minimum_duration_days"], 14)
        self.assertTrue(result["ready_to_launch"])
        self.assertEqual(result["stopping_criteria"]["decision_looks"], 1)

    def test_missing_guardrail_warns(self):
        issues = validate_design(design(guardrail_metrics=()))
        self.assertIn("missing_guardrail", {issue["code"] for issue in issues})
        self.assertFalse(any(issue["level"] == "error" for issue in issues))

    def test_duplicate_metric_blocks_launch(self):
        result = generate_design(design(secondary_metrics=(MetricDefinition("conversion"),)))
        self.assertFalse(result["ready_to_launch"])
        self.assertIn("duplicate_metric", {issue["code"] for issue in result["issues"]})

    def test_unvalidated_repeated_looks_block_launch(self):
        result = generate_design(design(planned_looks=4))
        self.assertFalse(result["ready_to_launch"])
        self.assertIn("unsupported_sequential", {issue["code"] for issue in result["issues"]})

    def test_traffic_can_extend_duration(self):
        self.assertGreater(generate_design(design(daily_eligible_users=1000))["minimum_duration_days"], 14)


if __name__ == "__main__":
    unittest.main()

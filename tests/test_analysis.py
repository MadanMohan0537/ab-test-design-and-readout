import unittest

from backend.app.analysis import analyze_experiment, analyze_novelty, analyze_segments
from backend.app.models import ArmResult, ExperimentDesign, ExperimentObservation, MetricDefinition, MetricResult


def design():
    return ExperimentDesign(
        hypothesis="Treatment increases conversion", control="old", treatment="new",
        primary_metric=MetricDefinition("conversion"), guardrail_metrics=(MetricDefinition("support", "decrease"),),
        baseline_rate=.08, expected_relative_lift=.05, daily_eligible_users=12000, minimum_days=14,
    )


def metric(name="conversion", cx=8100, cn=100000, tx=8800, tn=100000, direction="increase", threshold=None):
    return MetricResult(name, ArmResult(cn, cx), ArmResult(tn, tx), direction, threshold)


def observation(**overrides):
    values = dict(experiment_id="exp-1", primary=metric(), guardrails=(metric("support", 500, 100000, 620, 100000, "decrease", .002),), days_running=14, decision_looks=1)
    values.update(overrides)
    return ExperimentObservation(**values)


class AnalysisTests(unittest.TestCase):
    def test_recommends_ship_for_mature_valid_win(self):
        result = analyze_experiment(design(), observation())
        self.assertEqual(result["recommendation"], "ship")
        self.assertTrue(result["primary"]["significant"])
        self.assertFalse(result["guardrails"][0]["threshold_breached"])

    def test_srm_overrides_outcome(self):
        result = analyze_experiment(design(), observation(primary=metric(cn=120000, tn=80000, cx=9720, tx=7040)))
        self.assertEqual(result["recommendation"], "investigate")
        self.assertTrue(result["sample_ratio_mismatch"]["mismatch"])

    def test_early_readout_continues(self):
        result = analyze_experiment(design(), observation(primary=metric(cn=10000, tn=10000, cx=810, tx=900), days_running=5))
        self.assertEqual(result["recommendation"], "continue")

    def test_peeking_violation_requires_investigation(self):
        result = analyze_experiment(design(), observation(decision_looks=3))
        self.assertEqual(result["recommendation"], "investigate")
        self.assertTrue(result["maturity"]["unexpected_peeking"])

    def test_guardrail_breach_rejects(self):
        bad = metric("support", 500, 100000, 900, 100000, "decrease", .002)
        self.assertEqual(analyze_experiment(design(), observation(guardrails=(bad,)))["recommendation"], "reject")

    def test_harmful_primary_rejects(self):
        bad = metric(cx=9000, tx=8000)
        self.assertEqual(analyze_experiment(design(), observation(primary=bad))["recommendation"], "reject")

    def test_inconclusive_complete_test_iterates(self):
        flat = metric(cx=8100, tx=8120)
        self.assertEqual(analyze_experiment(design(), observation(primary=flat))["recommendation"], "iterate")

    def test_metric_contract_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "primary metric"):
            analyze_experiment(design(), observation(primary=metric("revenue")))
        with self.assertRaisesRegex(ValueError, "predeclared"):
            analyze_experiment(design(), observation(guardrails=(metric("latency"),)))

    def test_segments_use_multiple_comparison_correction(self):
        result = analyze_segments({"platform": (metric("ios"), metric("android"))}, .05)
        self.assertEqual(result["adjusted_alpha"], .025)
        self.assertEqual(result["comparisons"], 2)

    def test_novelty_requires_history_and_detects_decay(self):
        self.assertEqual(analyze_novelty(())["status"], "insufficient_data")
        rows = tuple({"control_visitors": 1000, "control_conversions": 80, "treatment_visitors": 1000, "treatment_conversions": value} for value in (110, 108, 106, 86, 84, 83))
        self.assertTrue(analyze_novelty(rows)["detected"])


if __name__ == "__main__":
    unittest.main()

import unittest

from backend.app.statistics import adjusted_alpha, sample_ratio_mismatch, sample_size_two_proportions, two_proportion_z_test


class StatisticsTests(unittest.TestCase):
    def test_sample_size_is_positive_and_repeatable(self):
        self.assertEqual(sample_size_two_proportions(.08, .05), 73853)

    def test_smaller_effect_requires_more_users(self):
        self.assertGreater(sample_size_two_proportions(.08, .03), sample_size_two_proportions(.08, .10))

    def test_invalid_sample_inputs_fail(self):
        for baseline, lift in ((0, .1), (1, .1), (.8, .5), (.1, 0)):
            with self.subTest(baseline=baseline, lift=lift), self.assertRaises(ValueError):
                sample_size_two_proportions(baseline, lift)

    def test_two_proportion_result(self):
        result = two_proportion_z_test(8100, 100000, 8800, 100000)
        self.assertAlmostEqual(result["control_rate"], .081)
        self.assertAlmostEqual(result["treatment_rate"], .088)
        self.assertGreater(result["relative_lift"], .08)
        self.assertLess(result["p_value"], .05)
        self.assertLess(result["difference_interval_95"][0], result["difference_interval_95"][1])

    def test_invalid_counts_fail(self):
        with self.assertRaises(ValueError):
            two_proportion_z_test(11, 10, 5, 10)
        with self.assertRaises(TypeError):
            two_proportion_z_test(1.5, 10, 5, 10)

    def test_balanced_assignment_has_no_srm(self):
        result = sample_ratio_mismatch(10000, 10000)
        self.assertFalse(result["mismatch"])
        self.assertEqual(result["p_value"], 1)

    def test_large_assignment_imbalance_has_srm(self):
        result = sample_ratio_mismatch(12000, 8000)
        self.assertTrue(result["mismatch"])
        self.assertLess(result["p_value"], .01)

    def test_bonferroni_alpha(self):
        self.assertEqual(adjusted_alpha(.05, 5), .01)


if __name__ == "__main__":
    unittest.main()

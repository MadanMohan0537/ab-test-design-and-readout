"""Deterministic statistical primitives using Python's standard library."""

import math
from statistics import NormalDist


NORMAL = NormalDist()


def validate_count(successes: int, total: int, label: str = "arm") -> None:
    if not isinstance(successes, int) or not isinstance(total, int):
        raise TypeError(f"{label} counts must be integers")
    if total <= 0 or successes < 0 or successes > total:
        raise ValueError(f"{label} requires 0 <= successes <= total and total > 0")


def two_proportion_z_test(control_successes: int, control_total: int, treatment_successes: int, treatment_total: int) -> dict:
    validate_count(control_successes, control_total, "control")
    validate_count(treatment_successes, treatment_total, "treatment")
    control_rate = control_successes / control_total
    treatment_rate = treatment_successes / treatment_total
    pooled = (control_successes + treatment_successes) / (control_total + treatment_total)
    standard_error_null = math.sqrt(max(pooled * (1 - pooled) * (1 / control_total + 1 / treatment_total), 0))
    z_score = (treatment_rate - control_rate) / standard_error_null if standard_error_null else 0.0
    p_value = 2 * (1 - NORMAL.cdf(abs(z_score)))
    standard_error_difference = math.sqrt(
        control_rate * (1 - control_rate) / control_total + treatment_rate * (1 - treatment_rate) / treatment_total
    )
    margin = NORMAL.inv_cdf(0.975) * standard_error_difference
    difference = treatment_rate - control_rate
    return {
        "control_rate": control_rate,
        "treatment_rate": treatment_rate,
        "absolute_difference": difference,
        "relative_lift": difference / control_rate if control_rate else None,
        "z_score": z_score,
        "p_value": p_value,
        "confidence": 1 - p_value,
        "difference_interval_95": [difference - margin, difference + margin],
    }


def sample_size_two_proportions(baseline: float, relative_lift: float, alpha: float = 0.05, power: float = 0.8) -> int:
    if not 0 < baseline < 1:
        raise ValueError("baseline must be between zero and one")
    if relative_lift == 0:
        raise ValueError("relative lift must not be zero")
    if not 0 < alpha < 0.5 or not 0.5 < power < 1:
        raise ValueError("alpha or power is outside the supported range")
    treatment = baseline * (1 + relative_lift)
    if not 0 < treatment < 1:
        raise ValueError("expected treatment rate must be between zero and one")
    pooled = (baseline + treatment) / 2
    z_alpha = NORMAL.inv_cdf(1 - alpha / 2)
    z_power = NORMAL.inv_cdf(power)
    numerator = (
        z_alpha * math.sqrt(2 * pooled * (1 - pooled))
        + z_power * math.sqrt(baseline * (1 - baseline) + treatment * (1 - treatment))
    ) ** 2
    return math.ceil(numerator / (treatment - baseline) ** 2)


def sample_ratio_mismatch(control_total: int, treatment_total: int, expected_treatment_share: float = 0.5) -> dict:
    if control_total < 0 or treatment_total < 0 or control_total + treatment_total == 0:
        raise ValueError("exposure counts must be non-negative with a positive total")
    if not 0 < expected_treatment_share < 1:
        raise ValueError("expected treatment share must be between zero and one")
    total = control_total + treatment_total
    expected = [total * (1 - expected_treatment_share), total * expected_treatment_share]
    observed = [control_total, treatment_total]
    chi_square = sum((actual - target) ** 2 / target for actual, target in zip(observed, expected))
    p_value = math.erfc(math.sqrt(chi_square / 2))
    return {"chi_square": chi_square, "p_value": p_value, "mismatch": p_value < 0.01, "observed_share": treatment_total / total, "expected_share": expected_treatment_share}


def adjusted_alpha(alpha: float, comparisons: int) -> float:
    if comparisons < 1:
        raise ValueError("comparisons must be positive")
    return alpha / comparisons

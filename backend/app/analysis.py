"""Validity checks, deterministic readout, and recommendation policy."""

from .models import ExperimentDesign, ExperimentObservation, MetricResult
from .statistics import adjusted_alpha, sample_ratio_mismatch, two_proportion_z_test


def analyze_metric(metric: MetricResult, alpha: float) -> dict:
    result = two_proportion_z_test(metric.control.conversions, metric.control.visitors, metric.treatment.conversions, metric.treatment.visitors)
    harmful = result["absolute_difference"] < 0 if metric.direction == "increase" else result["absolute_difference"] > 0
    result.update({"name": metric.name, "direction": metric.direction, "alpha": alpha, "significant": result["p_value"] < alpha, "harmful_direction": harmful})
    if metric.guardrail_threshold is not None:
        degradation = -result["absolute_difference"] if metric.direction == "increase" else result["absolute_difference"]
        result["threshold"] = metric.guardrail_threshold
        result["threshold_breached"] = degradation > metric.guardrail_threshold
    return result


def analyze_novelty(daily_primary: tuple[dict, ...]) -> dict:
    if len(daily_primary) < 6:
        return {"detected": False, "status": "insufficient_data", "message": "At least six daily observations are required."}
    midpoint = len(daily_primary) // 2
    def effect(rows):
        control_n = sum(row["control_visitors"] for row in rows)
        treatment_n = sum(row["treatment_visitors"] for row in rows)
        control = sum(row["control_conversions"] for row in rows) / control_n
        treatment = sum(row["treatment_conversions"] for row in rows) / treatment_n
        return treatment - control
    early = effect(daily_primary[:midpoint])
    late = effect(daily_primary[midpoint:])
    threshold = max(0.002, abs(early) * 0.5)
    detected = abs(early - late) > threshold and abs(early) > abs(late)
    return {"detected": detected, "status": "checked", "early_effect": early, "late_effect": late, "message": "The observed effect weakened materially over time." if detected else "No material novelty pattern was detected by the heuristic."}


def analyze_segments(segments: dict[str, tuple[MetricResult, ...]], alpha: float) -> dict:
    comparisons = sum(len(values) for values in segments.values())
    if not comparisons:
        return {"comparisons": 0, "adjusted_alpha": alpha, "results": []}
    corrected = adjusted_alpha(alpha, comparisons)
    results = []
    for dimension, values in segments.items():
        for metric in values:
            result = analyze_metric(metric, corrected)
            result["dimension"] = dimension
            results.append(result)
    return {"comparisons": comparisons, "adjusted_alpha": corrected, "method": "Bonferroni", "results": results}


def analyze_experiment(design: ExperimentDesign, observation: ExperimentObservation) -> dict:
    if observation.primary.name.lower() != design.primary_metric.name.lower():
        raise ValueError("observed primary metric does not match the predeclared design")
    declared_guardrails = {metric.name.lower() for metric in design.guardrail_metrics}
    observed_guardrails = {metric.name.lower() for metric in observation.guardrails}
    if observed_guardrails - declared_guardrails:
        raise ValueError("observed guardrail was not predeclared")
    primary = analyze_metric(observation.primary, design.alpha)
    srm = sample_ratio_mismatch(observation.primary.control.visitors, observation.primary.treatment.visitors, design.allocation)
    guardrails = [analyze_metric(metric, design.alpha / max(len(observation.guardrails), 1)) for metric in observation.guardrails]
    segment_analysis = analyze_segments(observation.segments, design.alpha)
    novelty = analyze_novelty(observation.daily_primary)
    required_total = design_result_total(design)
    observed_total = observation.primary.control.visitors + observation.primary.treatment.visitors
    maturity = {
        "required_total": required_total,
        "observed_total": observed_total,
        "sample_complete": observed_total >= required_total,
        "duration_complete": observation.days_running >= design.minimum_days,
        "unexpected_peeking": observation.decision_looks > design.planned_looks,
    }
    validity_issues = []
    if srm["mismatch"]:
        validity_issues.append("Sample-ratio mismatch detected; investigate assignment and logging before reading outcomes.")
    if maturity["unexpected_peeking"]:
        validity_issues.append("Decision looks exceeded the predeclared fixed-horizon plan.")
    if not maturity["sample_complete"] or not maturity["duration_complete"]:
        validity_issues.append("The predeclared sample size or minimum duration has not been reached.")
    breached = [metric for metric in guardrails if metric.get("threshold_breached")]
    if srm["mismatch"]:
        recommendation = "investigate"
        reason = "Assignment or exposure logging may be invalid because SRM was detected."
    elif maturity["unexpected_peeking"]:
        recommendation = "investigate"
        reason = "The fixed-horizon stopping rule was violated; do not use the nominal p-value for a ship decision."
    elif not maturity["sample_complete"] or not maturity["duration_complete"]:
        recommendation = "continue"
        reason = "Continue until both the planned sample and duration are complete."
    elif breached:
        recommendation = "reject"
        reason = f"Guardrail threshold breached: {', '.join(metric['name'] for metric in breached)}."
    elif primary["significant"] and not primary["harmful_direction"]:
        recommendation = "ship"
        reason = "The primary metric improved at the predeclared fixed-horizon threshold without a guardrail breach."
    elif primary["significant"] and primary["harmful_direction"]:
        recommendation = "reject"
        reason = "The primary metric moved significantly in the harmful direction."
    else:
        recommendation = "iterate"
        reason = "The experiment completed without clear evidence of the expected primary-metric improvement."
    return {
        "schema_version": "1.0.0",
        "experiment_id": observation.experiment_id,
        "primary": primary,
        "guardrails": guardrails,
        "sample_ratio_mismatch": srm,
        "maturity": maturity,
        "novelty": novelty,
        "segments": segment_analysis,
        "validity_issues": validity_issues,
        "recommendation": recommendation,
        "reason": reason,
        "calculation_policy": "deterministic-fixed-horizon-v1",
    }


def design_result_total(design: ExperimentDesign) -> int:
    from .design import generate_design
    return generate_design(design)["sample_size"]["total"]

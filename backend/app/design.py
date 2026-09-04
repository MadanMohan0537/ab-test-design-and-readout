"""Experiment design generation and preflight validation."""

import math

from .models import ExperimentDesign
from .statistics import sample_size_two_proportions


def validate_design(design: ExperimentDesign) -> list[dict]:
    issues = []
    if not design.hypothesis.strip():
        issues.append({"level": "error", "code": "missing_hypothesis", "message": "Define a falsifiable hypothesis before launch."})
    if not design.control.strip() or not design.treatment.strip() or design.control.strip() == design.treatment.strip():
        issues.append({"level": "error", "code": "invalid_arms", "message": "Control and treatment must be distinct and explicit."})
    metric_names = [design.primary_metric.name, *[metric.name for metric in design.secondary_metrics], *[metric.name for metric in design.guardrail_metrics]]
    if len(metric_names) != len(set(name.lower() for name in metric_names)):
        issues.append({"level": "error", "code": "duplicate_metric", "message": "A metric cannot occupy multiple decision roles."})
    if design.planned_looks != 1:
        issues.append({"level": "error", "code": "unsupported_sequential", "message": "The MVP supports one fixed-horizon decision look. Use a validated sequential method for repeated looks."})
    if design.minimum_days < 7:
        issues.append({"level": "warning", "code": "short_duration", "message": "Run through at least one full weekly cycle when seasonality may matter."})
    if not design.guardrail_metrics:
        issues.append({"level": "warning", "code": "missing_guardrail", "message": "Define at least one guardrail metric before launch."})
    return issues


def generate_design(design: ExperimentDesign) -> dict:
    sample_per_arm = sample_size_two_proportions(design.baseline_rate, design.expected_relative_lift, design.alpha, design.power)
    total_sample = math.ceil(sample_per_arm / min(design.allocation, 1 - design.allocation))
    traffic_duration = math.ceil(total_sample / max(design.daily_eligible_users, 1))
    duration_days = max(design.minimum_days, traffic_duration)
    issues = validate_design(design)
    return {
        "schema_version": "1.0.0",
        "design": design.to_dict(),
        "sample_size": {"per_arm": sample_per_arm, "total": total_sample},
        "minimum_duration_days": duration_days,
        "stopping_criteria": {
            "regime": "fixed_horizon",
            "decision_looks": 1,
            "readout_after_sample": total_sample,
            "readout_after_days": duration_days,
            "early_stop_for_harm": "Pause only for a predeclared severe guardrail breach; do not declare success early.",
        },
        "bias_checklist": [
            "Confirm randomization and analysis use the same unit.",
            "Run an A/A or assignment audit before high-impact experiments.",
            "Check sample-ratio mismatch before reading outcomes.",
            "Cover complete weekly cycles and known seasonal events.",
            "Do not change variants, metrics, or eligibility after launch.",
            "Do not stop a fixed-horizon test when a nominal p-value first crosses alpha.",
            "Predeclare segment analyses and correct for multiple comparisons.",
        ],
        "issues": issues,
        "ready_to_launch": not any(issue["level"] == "error" for issue in issues),
    }

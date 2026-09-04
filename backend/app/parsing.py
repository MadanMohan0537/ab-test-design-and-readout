"""JSON-to-domain parsing with explicit contracts."""

from .models import ArmResult, ExperimentDesign, ExperimentObservation, MetricDefinition, MetricResult


def metric_definition(data: dict) -> MetricDefinition:
    return MetricDefinition(name=str(data["name"]), direction=data.get("direction", "increase"), minimum_detectable_effect=float(data.get("minimum_detectable_effect", 0.05)), kind=data.get("kind", "binary"))


def experiment_design(data: dict) -> ExperimentDesign:
    return ExperimentDesign(
        hypothesis=str(data["hypothesis"]), control=str(data["control"]), treatment=str(data["treatment"]),
        primary_metric=metric_definition(data["primary_metric"]),
        secondary_metrics=tuple(metric_definition(item) for item in data.get("secondary_metrics", [])),
        guardrail_metrics=tuple(metric_definition(item) for item in data.get("guardrail_metrics", [])),
        baseline_rate=float(data["baseline_rate"]), expected_relative_lift=float(data["expected_relative_lift"]),
        alpha=float(data.get("alpha", 0.05)), power=float(data.get("power", 0.8)), allocation=float(data.get("allocation", 0.5)),
        daily_eligible_users=int(data.get("daily_eligible_users", 1000)), minimum_days=int(data.get("minimum_days", 14)),
        planned_looks=int(data.get("planned_looks", 1)), randomization_unit=data.get("randomization_unit", "user"),
    )


def metric_result(data: dict) -> MetricResult:
    return MetricResult(
        name=str(data["name"]), direction=data.get("direction", "increase"), guardrail_threshold=data.get("guardrail_threshold"),
        control=ArmResult(int(data["control"]["visitors"]), int(data["control"]["conversions"])),
        treatment=ArmResult(int(data["treatment"]["visitors"]), int(data["treatment"]["conversions"])),
    )


def observation(data: dict) -> ExperimentObservation:
    return ExperimentObservation(
        experiment_id=str(data["experiment_id"]), primary=metric_result(data["primary"]),
        guardrails=tuple(metric_result(item) for item in data.get("guardrails", [])),
        segments={dimension: tuple(metric_result(item) for item in items) for dimension, items in data.get("segments", {}).items()},
        days_running=int(data.get("days_running", 0)), decision_looks=int(data.get("decision_looks", 1)),
        daily_primary=tuple(data.get("daily_primary", [])),
    )

"""Typed domain models kept independent from the HTTP framework."""

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    direction: str = "increase"
    minimum_detectable_effect: float = 0.05
    kind: str = "binary"


@dataclass(frozen=True)
class ExperimentDesign:
    hypothesis: str
    control: str
    treatment: str
    primary_metric: MetricDefinition
    secondary_metrics: tuple[MetricDefinition, ...] = ()
    guardrail_metrics: tuple[MetricDefinition, ...] = ()
    baseline_rate: float = 0.08
    expected_relative_lift: float = 0.05
    alpha: float = 0.05
    power: float = 0.80
    allocation: float = 0.5
    daily_eligible_users: int = 1000
    minimum_days: int = 14
    planned_looks: int = 1
    randomization_unit: str = "user"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ArmResult:
    visitors: int
    conversions: int

    @property
    def rate(self) -> float:
        return self.conversions / self.visitors if self.visitors else 0.0


@dataclass(frozen=True)
class MetricResult:
    name: str
    control: ArmResult
    treatment: ArmResult
    direction: str = "increase"
    guardrail_threshold: float | None = None


@dataclass(frozen=True)
class ExperimentObservation:
    experiment_id: str
    primary: MetricResult
    guardrails: tuple[MetricResult, ...] = ()
    segments: dict[str, tuple[MetricResult, ...]] = field(default_factory=dict)
    days_running: int = 0
    decision_looks: int = 1
    daily_primary: tuple[dict, ...] = ()

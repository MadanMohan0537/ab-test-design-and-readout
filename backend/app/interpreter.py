"""Evidence-bound interpretation; no statistical calculation occurs here."""


def pct(value: float | None, signed: bool = False) -> str:
    if value is None:
        return "n/a"
    prefix = "+" if signed and value >= 0 else ""
    return f"{prefix}{value * 100:.2f}%"


def interpret(result: dict) -> dict:
    primary = result["primary"]
    guardrail_text = "No guardrail threshold was breached." if not any(item.get("threshold_breached") for item in result["guardrails"]) else "At least one predefined guardrail was breached."
    return {
        "headline": f"{primary['name']}: {pct(primary['control_rate'])} control vs {pct(primary['treatment_rate'])} treatment.",
        "effect": f"Absolute change {pct(primary['absolute_difference'], True)}; relative lift {pct(primary['relative_lift'], True)}; p={primary['p_value']:.4f}.",
        "guardrail_summary": guardrail_text,
        "recommendation": result["recommendation"],
        "reason": result["reason"],
        "confidence_language": "Statistically significant at the predeclared threshold." if primary["significant"] else "Not statistically significant at the predeclared threshold.",
        "caveat": "The recommendation applies the declared policy to observed associations; it does not establish general causal transport beyond the randomized population.",
    }

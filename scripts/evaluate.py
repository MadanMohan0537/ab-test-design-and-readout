#!/usr/bin/env python3
"""Run deterministic decision-policy acceptance cases."""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.analysis import analyze_experiment
from backend.app.parsing import experiment_design, observation


def main() -> int:
    fixture = json.loads((ROOT / "examples" / "social-proof-result.json").read_text())
    cases = json.loads((ROOT / "evaluation" / "cases.json").read_text())
    failures = []
    for case in cases:
        payload = copy.deepcopy(fixture)
        for path, value in case.get("overrides", {}).items():
            target = payload
            parts = path.split(".")
            for part in parts[:-1]:
                target = target[int(part)] if part.isdigit() else target[part]
            target[parts[-1]] = value
        result = analyze_experiment(experiment_design(payload["design"]), observation(payload["observation"]))
        actual = result["recommendation"]
        marker = "PASS" if actual == case["expected"] else "FAIL"
        print(f"{marker} {case['name']}: expected={case['expected']} actual={actual}")
        if marker == "FAIL":
            failures.append(case["name"])
    print(f"\n{len(cases) - len(failures)}/{len(cases)} policy cases passed")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

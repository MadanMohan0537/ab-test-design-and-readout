# Product requirements

## Problem

Product teams can calculate a p-value yet still ship a weak experiment: the hypothesis is vague, metrics change after launch, sample size is underpowered, assignment is broken, or a guardrail is ignored. The Copilot turns those scattered decisions into one auditable lifecycle.

## MVP user and job

The primary user is a Product Manager running a binary-outcome A/B test. Their job is to move from hypothesis to a defensible decision without outsourcing arithmetic to an LLM.

## Requirements

1. Generate a preflight design with explicit arms, metric roles, sample size, duration, risks, and stopping rules.
2. Block unsupported repeated-look designs and contradictory metric contracts.
3. Analyze aggregated binary outcomes with deterministic code.
4. Check sample-ratio mismatch, maturity, guardrails, peeking, novelty, and segments.
5. Return an evidence-linked `ship`, `continue`, `iterate`, `reject`, or `investigate` recommendation.
6. Keep language generation downstream of computed facts.
7. Run locally with no paid API or hosted dependency.

## Non-goals

- Replacing an experimentation platform or event pipeline
- Claiming causal validity when randomization or instrumentation is broken
- Sequential testing, CUPED, continuous metrics, or Bayesian decisions in the MVP
- Letting an LLM calculate statistics or override policy

## Acceptance criteria

- Every recommendation is reproducible from the JSON input.
- A result cannot be read before sample and duration maturity without returning `continue`.
- SRM or unplanned peeking overrides a positive outcome with `investigate`.
- A breached guardrail prevents `ship`.
- The reference policy cases and unit tests pass in CI.

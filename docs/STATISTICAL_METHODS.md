# Statistical methods and decision policy

## Implemented methods

- Two-sided pooled z-test for two independent proportions
- Normal-approximation sample size for equal-sized two-arm binary experiments
- Chi-square sample-ratio-mismatch check with one degree of freedom
- Bonferroni correction for exploratory segment comparisons
- Fixed-horizon stopping with a single planned decision look
- Heuristic novelty warning comparing early and late absolute effects

The calculator uses `NormalDist` from Python's standard library, making results deterministic and keeping the runtime free of paid services.

## Precedence

| Condition | Recommendation |
|---|---|
| Sample-ratio mismatch | `investigate` |
| Unplanned decision looks | `investigate` |
| Sample or minimum duration incomplete | `continue` |
| Guardrail threshold breached | `reject` |
| Significant beneficial primary effect | `ship` |
| Significant harmful primary effect | `reject` |
| Otherwise | `iterate` |

This precedence prevents an attractive primary result from hiding invalid assignment, an incomplete test, or product harm.

## Limitations

The normal approximation is not appropriate for very sparse outcomes or small samples. Segment checks are exploratory and do not establish heterogeneous treatment effects. The novelty detector is a warning heuristic, not a longitudinal causal model. The MVP does not implement variance reduction, sequential inference, cluster randomization, continuous outcomes, non-inferiority, or Bayesian decisions.

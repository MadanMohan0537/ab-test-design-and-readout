# A/B Test Design and Readout

[![CI](https://github.com/MadanMohan0537/ab-test-design-and-readout/actions/workflows/ci.yml/badge.svg)](https://github.com/MadanMohan0537/ab-test-design-and-readout/actions/workflows/ci.yml)

**Plan a two-arm A/B test before launch, then read it out with validity checks first.** The readout ends in `ship`, `continue`, `iterate`, `reject`, or `investigate`, plus the reason for that call.

This repository was renamed from `ai-experimentation-copilot`. The Python package name in `pyproject.toml` is still `ai-experimentation-copilot`. The FastAPI title, the HTML page title, and the `/api/health` field `service` still use that old name. The Compose service key is still `copilot`. Those names are unchanged.

There is no language model in this code. Sample size, tests, and the recommendation are deterministic Python in the standard library. `backend/app/interpreter.py` only formats fields already on the result. `.env.example` comments an `OPENAI_API_KEY`; no module reads it.

## Problem and who it's for

`docs/PRD.md` describes the user as a product manager running a binary-outcome A/B test. The failure mode it calls out is a p-value with a weak experiment around it: a vague hypothesis, metrics that change after launch, an underpowered sample, broken assignment, or an ignored guardrail.

This repo turns that into one local design-and-readout flow. It does not replace an experimentation platform or an event pipeline.

## Approach

1. **Design preflight.** The parser requires a hypothesis, distinct control and treatment, a primary metric name, a baseline rate, and an expected relative lift. Missing those fields returns HTTP 422. Blocking issues, which set `ready_to_launch` to false, are a blank hypothesis, identical or blank arms, a metric name used in more than one role, and `planned_looks` other than 1. A missing guardrail, or `minimum_days` under 7, is a warning only. Secondary metrics are optional. `randomization_unit` defaults to `"user"` and is stored, not tested. `minimum_detectable_effect` defaults to `0.05` on each metric and is not an input to the sample-size formula.

2. **Planning.** `sample_size_two_proportions` is a normal approximation for an equal-sized, two-arm binary test, using the baseline rate, expected relative lift, alpha (default 0.05), and power (default 0.80). The returned total is `ceil(per_arm / min(allocation, 1 - allocation))`, so a split other than 50/50 increases the total. Minimum duration is the greater of `minimum_days` and the days needed to collect that total at `daily_eligible_users`. The stopping payload is fixed-horizon with one decision look. It does not run a sequential test. A plan with more than one look is marked not ready.

3. **Readout policy**, in `backend/app/analysis.py`, top to bottom. Validity problems win over a small p-value:

| Priority | Condition | Decision |
|---:|---|---|
| 1 | Sample-ratio mismatch: chi-square (1 df) p-value under 0.01 | `investigate` |
| 2 | `decision_looks` greater than `planned_looks` | `investigate` |
| 3 | Observed visitors below the planned total, or `days_running` below `minimum_days` | `continue` |
| 4 | A guardrail's absolute degradation is greater than its threshold | `reject` |
| 5 | Primary result significant and not in the harmful direction | `ship` |
| 6 | Primary result significant and in the harmful direction | `reject` |
| 7 | Completed, and none of the above | `iterate` |

   The duration check uses the design's `minimum_days`. It does not re-check the traffic-extended `minimum_duration_days` from the design response. A guardrail reject uses the threshold, not the guardrail p-value. Guardrail tests use alpha divided by the number of observed guardrails.

4. **Exploration.** Segment comparisons use a Bonferroni alpha (`alpha / comparisons`). The early-versus-late novelty check needs at least six daily rows and only warns. Neither segments nor novelty changes the recommendation.

5. **Explanation.** `interpret` copies `recommendation` and `reason`, and formats rates already on the result. It does not recompute the z-test or change the decision. The narrative prints `p` to four decimal places, so a very small p-value can appear as `p=0.0000` while `primary.p_value` keeps the full figure.

JSON Schema files in `schema/` describe the contracts. The API does not load them. Requests are parsed in `backend/app/parsing.py`.

## What exists today

- A FastAPI app: `POST /api/design`, `POST /api/analyze`, `GET /api/health`, `GET /` (the page), and FastAPI's `/docs`. Static files are mounted at `/assets`.
- A small browser page that follows the system light/dark scheme (`prefers-color-scheme`). Several request fields are fixed in `frontend/app.js` (arm labels, alpha, power, allocation, and the guardrail and segment counts sent on analyze).
- Optional bearer auth. If `API_TOKEN` is unset, `/api/design` and `/api/analyze` are open. If it is set, those routes require `Authorization: Bearer <token>` and return 401 otherwise. The page does not send that header. `/api/health` is not behind the check.
- `Dockerfile` and `docker-compose.yml`. The Compose service is `copilot` and publishes port 8000. Compose passes `API_TOKEN` through. `HOST` and `PORT` in `.env.example` are not read by the app or by Compose.
- **23** unit tests in `tests/` (`python -m unittest discover -s tests -v`) and **6** acceptance cases in `evaluation/cases.json` (`python scripts/evaluate.py`). Both commands passed on this checkout (Python 3.12.3): 23 tests, then `6/6 policy cases passed`. The six cases expect `ship`, `continue`, `investigate` (sample-ratio mismatch), `investigate` (extra decision looks), `reject` (guardrail threshold), and `iterate`. A harmful primary result is covered by a unit test, not by those six cases.
- CI (`.github/workflows/ci.yml`) on push and pull request runs `python -m compileall -q backend scripts tests`, the unit tests, and `python scripts/evaluate.py`. It does not start the server or check `frontend/app.js`.

Example files, called against a local server:

- `examples/social-proof-design.json` (8% baseline, 5% relative lift, 50/50 split, 12,000 eligible users per day, `minimum_days` 14) returns **73,853 users per arm**, **147,706 total**, and **`minimum_duration_days` 14**. Traffic alone would be 13 days (`ceil(147706 / 12000)`); 14 is the configured minimum. `ready_to_launch` is true.
- `examples/social-proof-result.json` (8,100 / 100,000 vs 8,800 / 100,000, so 8.10% vs 8.80%) returns **`ship`**. `primary.p_value` is about **1.827e-8**. The support-ticket rate rises from 0.50% to 0.62% (absolute increase 0.0012). That is under the 0.002 threshold, so `threshold_breached` is false even though the guardrail test itself is significant and in the harmful direction. The file has no `daily_primary`, so novelty is `insufficient_data`. The two platform segments are reported with adjusted alpha 0.025 and do not change `ship`.

## How success would be measured

`docs/METRICS.md` names intended measures and MVP targets: design completion, decision reproducibility, policy-case accuracy, invalid-readout interception, evidence coverage, and time to design. This repository does not contain measured results for any of them.

| Measure | Status |
|---|---|
| Design completion | Not yet measured |
| Decision reproducibility | Not yet measured |
| Policy-case accuracy | Not yet measured |
| Invalid-readout interception | Not yet measured |
| Evidence coverage | Not yet measured |
| Time to design | Not yet measured |

The unit tests and the six acceptance cases check the code. They are not a measurement of experiments in use.

## Limitations

- Two arms, one fixed-horizon look, and binary visitor/conversion counts. There is no continuous metric, sequential design, CUPED, cluster randomization, or multi-arm test. `kind` defaults to `"binary"` and the tests do not branch on it.
- The normal approximation is a poor fit for very small or sparse samples.
- Segment output is exploratory. The novelty check is a heuristic and needs six daily rows.
- The readout's duration gate is `minimum_days`, not the longer traffic-based duration the design response may show.
- JSON Schema files are not applied at request time.
- This is decision support on aggregated counts. It does not repair broken assignment, missing exposure events, interference, or a bad metric definition.

See [docs/STATISTICAL_METHODS.md](docs/STATISTICAL_METHODS.md), [docs/PRD.md](docs/PRD.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/METRICS.md](docs/METRICS.md).

## Quick start

Requires Python 3.11+ as declared in `pyproject.toml` (CI and the Docker image use 3.12).

```bash
git clone https://github.com/MadanMohan0537/ab-test-design-and-readout.git
cd ab-test-design-and-readout
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/evaluate.py
uvicorn backend.app.main:app --reload       # UI at http://localhost:8000, API docs at /docs
```

In a second terminal:

```bash
curl -X POST http://localhost:8000/api/design  -H 'Content-Type: application/json' --data-binary @examples/social-proof-design.json
curl -X POST http://localhost:8000/api/analyze -H 'Content-Type: application/json' --data-binary @examples/social-proof-result.json
```

If `API_TOKEN` is set, add `-H "Authorization: Bearer $API_TOKEN"` to those curls.

Local container (not a Workers deploy): `cp .env.example .env && docker compose up --build`, then open `http://localhost:8000`.

## Deployment

Cloudflare Workers is the planned deploy target, using `npx wrangler deploy`. This repository is not configured for Workers, and it is not deployed. There is no `wrangler.toml`, no Worker entry point, and no Worker name, so there is no live `workers.dev` URL to keep.

Before that command can publish this service, the repo needs:

- a `wrangler.toml`
- a Worker entry point
- for this Python code, either Cloudflare Python Workers or a JavaScript/TypeScript port of the API

## Which experimentation repo should I read?

| Repo | Use it for |
|---|---|
| **ab-test-design-and-readout** (this one) | Frequentist design preflight, validity-first readout, Python API. No language model. |
| [bayesian-ab-test-advisor](https://github.com/MadanMohan0537/bayesian-ab-test-advisor) | Bayesian analysis with expected loss. That repo's decision rules include ship, hold, and keep-running. |
| [experiment-decision-workspace](https://github.com/MadanMohan0537/experiment-decision-workspace) | A browser workspace. That repo's README says experiment drafts and human review decisions stay in browser `localStorage`. |

## License

[MIT](LICENSE)

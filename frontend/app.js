const byId = id => document.getElementById(id);
let currentDesign;

function designPayload() {
  return {
    hypothesis: byId("hypothesis").value,
    control: "Existing pricing page",
    treatment: "Pricing page with customer logos and testimonial",
    primary_metric: { name: byId("metric").value, direction: "increase", minimum_detectable_effect: Number(byId("lift").value) },
    secondary_metrics: [{ name: "Pricing CTA click-through", direction: "increase" }],
    guardrail_metrics: [{ name: byId("guardrail").value, direction: "decrease" }],
    baseline_rate: Number(byId("baseline").value),
    expected_relative_lift: Number(byId("lift").value),
    alpha: 0.05,
    power: 0.8,
    allocation: 0.5,
    daily_eligible_users: Number(byId("traffic").value),
    minimum_days: Number(byId("minDays").value),
    planned_looks: 1,
    randomization_unit: "user"
  };
}

async function post(path, body) {
  const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

async function generateDesign() {
  try {
    currentDesign = designPayload();
    const result = await post("/api/design", { design: currentDesign });
    byId("perArm").textContent = result.sample_size.per_arm.toLocaleString();
    byId("totalSample").textContent = result.sample_size.total.toLocaleString();
    byId("duration").textContent = result.minimum_duration_days;
    byId("launch").textContent = result.ready_to_launch ? "Ready" : "Blocked";
    byId("designDetails").classList.remove("empty");
    byId("designDetails").innerHTML = `<div class="contract"><div><b>Control</b><span>${result.design.control}</span></div><div><b>Treatment</b><span>${result.design.treatment}</span></div><div><b>Primary metric</b><span>${result.design.primary_metric.name}</span></div><div><b>Stopping rule</b><span>One fixed-horizon decision look</span></div></div><ul class="list">${result.bias_checklist.map(item => `<li>${item}</li>`).join("")}</ul>${result.issues.map(issue => `<div class="check ${issue.level === "error" ? "bad" : "warn"}"><b>${issue.code.replaceAll("_", " ")}</b><span>${issue.message}</span></div>`).join("")}`;
    byId("designError").textContent = "";
  } catch (error) { byId("designError").textContent = error.message; }
}

function observation() {
  const controlN = Number(byId("controlN").value);
  const variantN = Number(byId("variantN").value);
  return {
    experiment_id: "social-proof-pricing-v1",
    primary: { name: byId("metric").value, direction: "increase", control: { visitors: controlN, conversions: Number(byId("controlX").value) }, treatment: { visitors: variantN, conversions: Number(byId("variantX").value) } },
    guardrails: [{ name: byId("guardrail").value, direction: "decrease", guardrail_threshold: 0.002, control: { visitors: controlN, conversions: Math.round(controlN * .005) }, treatment: { visitors: variantN, conversions: Math.round(variantN * .0062) } }],
    days_running: Number(byId("daysRunning").value),
    decision_looks: Number(byId("looks").value),
    segments: {
      platform: [
        { name: "Android", direction: "increase", control: { visitors: Math.round(controlN * .4), conversions: Math.round(controlN * .4 * .078) }, treatment: { visitors: Math.round(variantN * .4), conversions: Math.round(variantN * .4 * .087) } },
        { name: "Web", direction: "increase", control: { visitors: Math.round(controlN * .6), conversions: Math.round(controlN * .6 * .083) }, treatment: { visitors: Math.round(variantN * .6), conversions: Math.round(variantN * .6 * .089) } }
      ]
    }
  };
}

function percent(value, signed = false) {
  return `${signed && value >= 0 ? "+" : ""}${(value * 100).toFixed(2)}%`;
}

async function runAnalysis() {
  try {
    currentDesign ||= designPayload();
    const result = await post("/api/analyze", { design: currentDesign, observation: observation() });
    byId("controlRate").textContent = percent(result.primary.control_rate);
    byId("variantRate").textContent = percent(result.primary.treatment_rate);
    byId("relativeLift").textContent = percent(result.primary.relative_lift, true);
    byId("pValue").textContent = `p=${result.primary.p_value.toFixed(4)}`;
    byId("recommendation").textContent = result.recommendation;
    byId("headline").textContent = result.interpretation.headline;
    byId("confidence").textContent = result.interpretation.confidence_language;
    byId("effect").textContent = result.interpretation.effect;
    const checks = [
      { name: "Sample ratio", good: !result.sample_ratio_mismatch.mismatch, text: result.sample_ratio_mismatch.mismatch ? "Mismatch detected" : "Allocation looks valid" },
      { name: "Planned sample", good: result.maturity.sample_complete, text: `${result.maturity.observed_total.toLocaleString()} / ${result.maturity.required_total.toLocaleString()}` },
      { name: "Minimum duration", good: result.maturity.duration_complete, text: result.maturity.duration_complete ? "Completed" : "Not completed" },
      { name: "Guardrails", good: !result.guardrails.some(item => item.threshold_breached), text: result.interpretation.guardrail_summary }
    ];
    byId("checks").innerHTML = checks.map(check => `<div class="check ${check.good ? "good" : "bad"}"><b>${check.name}</b><span>${check.text}</span></div>`).join("");
    byId("decision").textContent = result.recommendation.toUpperCase();
    byId("reason").textContent = result.reason;
    byId("caveat").textContent = result.interpretation.caveat;
    byId("analysisError").textContent = "";
  } catch (error) { byId("analysisError").textContent = error.message; }
}

document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(item => item.classList.toggle("active", item === tab));
  byId("designPanel").classList.toggle("hidden", tab.dataset.tab !== "design");
  byId("analyzePanel").classList.toggle("hidden", tab.dataset.tab !== "analyze");
}));
byId("createDesign").addEventListener("click", generateDesign);
byId("runAnalysis").addEventListener("click", runAnalysis);

# Day 23 Lab Reflection

> Fill in each section. Grader reads the "What I'd change" paragraph closest.

**Student:** Nguyen Minh Hieu
**Submission date:** 2026-06-29
**Lab repo URL:** https://github.com/minhhieu29/Day23-2A202600705-NguyenMinhHieu

---

## 1. Hardware + setup output

Paste output of `python3 00-setup/verify-docker.py`:

```json
{
  "docker": {
    "ok": true,
    "version": "29.5.3"
  },
  "compose_v2": {
    "ok": true,
    "version": "5.1.4"
  },
  "ram_gb_available": 7.56,
  "ram_ok": true,
  "required_ports": [
    8000,
    9090,
    9093,
    3000,
    3100,
    16686,
    4317,
    4318,
    8888
  ],
  "bound_ports": [],
  "all_ports_free": true
}
```

---

## 2. Track 02 — Dashboards & Alerts

### 6 essential panels (screenshot)

Drop `submission/screenshots/dashboard-overview.png`.

*(Completed and visible in Grafana: active inference requests gauge, rate/throughput, 99th percentile latency, token usage/cost counters, GPU utilization gauge, and average response quality score)*

### Burn-rate panel

Drop `submission/screenshots/slo-burn-rate.png`.

*(Completed and visible in Grafana: Burn Rate 1h/6h panels mapping SLO Fast/Slow burn alerts)*

### Alert fire + resolve

| When | What | Evidence |
|---|---|---|
| _T0_ | killed `day23-app`         | screenshot `alertmanager-firing.png` |
| _T0+90s_ | `ServiceDown` fired   | screenshot `slack-firing.png` |
| _T1_ | restored app              | — |
| _T1+60s_ | alert resolved        | screenshot `slack-resolved.png` |

*(Captured in `submission/webhook-events.log` with correct channel `#oncall` and Slack webhook formatting)*

### One thing surprised me about Prometheus / Grafana

I was surprised by how strictly Alertmanager validates Slack API mock responses. Returning `OK` (uppercase) instead of `ok` (lowercase) is treated as an unrecoverable failure, which prevents the dispatcher from successfully acknowledging the notification and blocks future resolution notifications for that alert group. Getting this detail right is crucial for webhook mock reliability.

---

## 3. Track 03 — Tracing & Logs

### One trace screenshot from Jaeger

Drop `submission/screenshots/jaeger-trace.png` showing `embed-text → vector-search → generate-tokens` spans.

### Log line correlated to trace

Paste the log line and the trace_id it links to:

```json
{"level": "info", "message": "inference request completed", "trace_id": "cb7a43e4f71e8477464303b6d05f32b8", "latency_ms": 18}
```

### Tail-sampling math

If your service produced N traces/sec, what fraction did the policy keep? Show the calculation.

Let $N$ be the total traces per second. Let $E$ be the number of error traces per second. Let $S$ be the number of slow traces per second (>2s latency).
Assuming the sets $E$ and $S$ of traces kept by the status code and latency policies are represented as $T_{always\_keep} = E \cup S$:
The remaining healthy and fast traces are $N - (E \cup S)$, which are subject to the 1% probabilistic sampling policy.

The fraction kept by the collector is:
$$\text{Fraction Kept} = \frac{|E \cup S| + 0.01 \times (N - |E \cup S|)}{N}$$

For example, if all $N$ traces are healthy and fast ($|E \cup S| = 0$), the collector keeps exactly **1%** ($0.01$) of the total traces.

---

## 4. Track 04 — Drift Detection

### PSI scores

Paste `04-drift-detection/reports/drift-summary.json`:

```json
{
  "prompt_length": {
    "psi": 3.461,
    "kl": 1.7982,
    "ks_stat": 0.702,
    "ks_pvalue": 0.0,
    "drift": "yes"
  },
  "embedding_norm": {
    "psi": 0.0187,
    "kl": 0.0324,
    "ks_stat": 0.052,
    "ks_pvalue": 0.133853,
    "drift": "no"
  },
  "response_length": {
    "psi": 0.0162,
    "kl": 0.0178,
    "ks_stat": 0.056,
    "ks_pvalue": 0.086899,
    "drift": "no"
  },
  "response_quality": {
    "psi": 8.8486,
    "kl": 13.5011,
    "ks_stat": 0.941,
    "ks_pvalue": 0.0,
    "drift": "yes"
  }
}
```

### Which test fits which feature?

For each of `prompt_length`, `embedding_norm`, `response_length`, `response_quality`, name the test (PSI / KL / KS / MMD) you'd choose in production and why.

- **`prompt_length`**: **KS (Kolmogorov-Smirnov) test** or **PSI (Population Stability Index)**. Since length is a 1D continuous numerical value, KS is great because it compares cumulative distribution functions without requiring arbitrary binning.
- **`embedding_norm`**: **PSI**. It is the industry standard for continuous value drift because it has stable, well-understood thresholds (e.g. >0.2 indicates significant drift) and is highly interpretable. For high-dimensional embeddings directly, **MMD (Maximum Mean Discrepancy)** is the best choice as it directly computes distance between multivariate distributions.
- **`response_length`**: **KS test** or **PSI**. Similar to prompt length, response length is a 1D numeric feature where KS test is highly sensitive to statistical shifts.
- **`response_quality`**: **PSI**. Since quality scores are often heavily binned or evaluated against custom thresholds, PSI is ideal as it measures the stability of the distribution across distinct quality categories and bins.

---

## 5. Track 05 — Cross-Day Integration

### Which prior-day metric was hardest to expose? Why?

The **Day 22 evaluation pass rate (`day22_dpo_eval_pass_rate`)** or the database metrics from Qdrant would be the hardest to expose. Instrumenting external systems like Qdrant requires deploying custom database exporters or database middleware drivers, which is far more complex than instrumenting application-level metrics directly inside the model serving logic.

---

## 6. The single change that mattered most

> **Grader reads this closest.** What one thing about your stack design — a metric you added, a label you dropped, a panel you reorganized, an alert threshold you tuned — made the biggest difference between "works" and "useful"? Write 1-2 paragraphs. Connect it to a concept from the deck.

The single design choice that made the biggest difference was adding **exemplars (tracing correlation)** directly to the Prometheus metrics. By appending the `trace_id` as an exemplar context to high-latency metrics (`inference_latency_seconds_bucket`), we bridged the gap between macro-level alerts and micro-level debugging.

In production, a "P99 latency > 2s" alert tells you *that* something is wrong, but it doesn't tell you *why*. By clicking on the exemplar in the Grafana panel and jumping directly to the corresponding Jaeger trace (`embed-text` -> `vector-search` -> `generate-tokens`), the operator can instantly isolate which step (e.g. Qdrant vector retrieval bottleneck vs. LLM generation slowness) caused the outlier. This aligns perfectly with the concept of **observability-driven development**, transforming raw, disconnected telemetry into an actionable diagnostic path.

---

## 7. AgentOps (Bonus)

### Why $pass^k \neq pass@k$ is important for your agent

$pass@k$ measures the static probability of obtaining a correct solution across $k$ independent candidate paths generated offline (e.g., standard code generation). In contrast, $pass^k$ is a dynamic agentic metric: it is the probability of a ReAct agent successfully correcting its errors and reaching the goal given $k$ iterative attempts or steps within the environment (using loop detection, tool recovery, and retry mechanisms). 

Understanding this difference is critical for optimizing agent design: it tells us that merely generating more static candidates ($pass@k$) is often less cost-effective than investing in structured, multi-step error correction, loop avoidance, and tool resilience policies ($pass^k$).

### Which SLI would you alert first?

The first SLI I would alert on is **`loops_detected`** (or a sustained increase in **`avg_steps_per_task`** nearing the step limit). An infinite loop indicates that the agent is stuck in an unproductive cycle (calling tools incorrectly or hallucinating arguments), generating excessive token costs and consuming system resources without ever making progress. Alerting on this first protects the operational budget and prevents runaway agent execution.

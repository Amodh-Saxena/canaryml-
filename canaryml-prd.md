# CanaryML: Zero-Downtime Model Rollout with Automated Canary Analysis

Product Requirements Document (PRD) for a portfolio project. Owner: Amodh. Status: Draft v1.

---

## 1. Overview

**One-line summary:** A Kubernetes setup that serves an ML model, releases a new model version to 10% of traffic first, compares its live metrics against the current version, and automatically promotes or rolls back with no human involved.

**Problem:** Offline accuracy does not guarantee production behavior. A new model can be slower, throw errors, or be less accurate on live traffic. Shipping it to 100% of users at once makes every regression a full outage.

**Solution:** Progressive delivery. The new version (canary) receives a small slice of traffic. Prometheus metrics are checked automatically at each step. If any gate fails, traffic goes back to the stable version.

### Goals
1. Serve two model versions side by side behind one URL with weighted traffic (10% / 50% / 100%).
2. Gate each step on three metrics: accuracy, p95 latency, error rate.
3. Roll back automatically when a gate fails, and promote automatically when all pass.
4. Show it working with a deliberately bad model (rollback) and a good model (promotion).
5. Automate build, test and image publishing with GitHub Actions.

### Non-goals
- Production-grade security, multi-cluster, or cloud deployment.
- Real delayed-label feedback. Ground-truth labels are simulated (see 6.1).
- Training a state-of-the-art model. The model is deliberately simple.

---

## 2. Success Criteria (must be measurable)

| # | Criterion | How to verify |
|---|---|---|
| 1 | A bad model (v2-bad) is rolled back automatically | Rollout status shows Degraded or aborted, 100% traffic on v1 |
| 2 | A good model (v3-good) is promoted automatically | Rollout reaches 100% on v3 |
| 3 | Time from bad release to rollback is recorded | Stopwatch or timestamps in the Argo Rollouts event log |
| 4 | Zero failed requests for users during the bad rollout | Load-test output shows error rate on stable traffic = 0% |
| 5 | CI blocks broken code | A failing test makes the GitHub Actions run fail |
| 6 | Everything reproducible from the README in under 30 min | A fresh clone plus `make up` works |

Record real numbers (accuracy of each version, rollback time, request counts). Do not invent any.

---

## 3. Technology Stack

| Layer | Tool | Language / format | Why |
|---|---|---|---|
| Model | scikit-learn (TF-IDF + Logistic Regression) | Python 3.11 | Fast to train, easy to make a "bad" version |
| Model API | FastAPI + Uvicorn | Python | Standard ML serving layer |
| Metrics in app | prometheus-client | Python | Exposes `/metrics` |
| Container | Docker | Dockerfile | Packaging |
| Local cluster | kind (Kubernetes in Docker) | YAML | Free local Kubernetes |
| Progressive delivery | Argo Rollouts | YAML (Rollout, AnalysisTemplate CRDs) | Canary steps and automated analysis |
| Traffic splitting | ingress-nginx (with Argo Rollouts NGINX traffic routing) | YAML | Exact weighted routing (10% means 10%) |
| Metrics collection | Prometheus via kube-prometheus-stack (Helm) | YAML / Helm values | Scrapes the app and feeds analysis |
| Dashboards | Grafana (ships with the stack) | JSON dashboard | Visual proof |
| Load / replay traffic | Python script with httpx (or Locust) | Python | Sends labeled evaluation traffic |
| CI | GitHub Actions | YAML | Lint, test, build, push image |
| Registry | GitHub Container Registry (ghcr.io) | n/a | Free image hosting |
| Lint / validation | ruff, pytest, kubeconform | n/a | Catches errors before deploy |
| Automation | Make + Bash | Makefile, shell | One-command setup |

**Versions:** Do not hard-code versions from memory. Look up the current stable version of each tool in its official docs at build time and pin it in a `VERSIONS.md` file.

---

## 4. Architecture

```
                 replay.py (labeled traffic)
                          |
                          v
                 ingress-nginx  (weighted: stable 90 / canary 10)
                    |                    |
                    v                    v
             Service: stable      Service: canary
                    |                    |
              Pods: model v1       Pods: model v2
                    |                    |
                    +---> /metrics <-----+
                              |
                         Prometheus  <--- ServiceMonitor
                              |
                      Argo Rollouts AnalysisRun
                  (accuracy, p95 latency, error rate)
                              |
                  pass -> next step     fail -> rollback
                              |
                           Grafana (dashboards)
```

CI flow: push to GitHub, then lint and test, then build Docker image, then push to ghcr.io. Deployment to the local kind cluster is done with `make deploy VERSION=...`, because GitHub-hosted runners cannot reach a laptop cluster.

---

## 5. Repository Structure

```
canaryml/
  app/
    main.py              # FastAPI app: /predict, /healthz, /metrics
    metrics.py           # Prometheus counters and histograms
    model_loader.py      # loads the model file named by MODEL_PATH
  training/
    train.py             # trains v1, v2-bad, v3-good; writes models/*.joblib and models/report.json
  models/                # generated .joblib files (git-ignored) and report.json (committed)
  tests/
    test_api.py
    test_model_quality.py
  traffic/
    replay.py            # sends labeled requests at a steady rate
  k8s/
    kind-config.yaml
    namespace.yaml
    rollout.yaml         # Argo Rollout with canary steps
    services.yaml        # stable and canary Services
    ingress.yaml         # stable Ingress (Argo creates the canary Ingress)
    analysis-template.yaml
    servicemonitor.yaml
  monitoring/
    values.yaml          # kube-prometheus-stack Helm values
    grafana-dashboard.json
  .github/workflows/
    ci.yaml
  Dockerfile
  Makefile
  requirements.txt
  VERSIONS.md
  README.md
```

---

## 6. Functional Requirements

### 6.1 Model API
- `POST /predict` takes `{"text": "...", "true_label": 0|1 (optional)}` and returns `{"label": 0|1, "model_version": "..."}`.
- `true_label` is an evaluation-only field. When present, the app records whether the prediction was correct. This simulates labeled feedback. In a real system, labels arrive later, and that limitation should be stated in the README.
- `GET /healthz` returns 200 when the model is loaded.
- `GET /metrics` exposes Prometheus metrics.
- Environment variables: `MODEL_PATH`, `MODEL_VERSION`.
- Optional `FAULT_LATENCY_MS` and `FAULT_ERROR_RATE` env vars to inject latency or errors for extra failure demos.

### 6.2 Metrics (names are fixed so queries match)
- `http_requests_total{status}`: counter
- `http_request_duration_seconds`: histogram (p95 from buckets)
- `model_predictions_total{model_version, correct="true|false"}`: counter, incremented only when `true_label` is provided

### 6.3 Model versions
| Version | Purpose | How to build it |
|---|---|---|
| v1 | Stable baseline | TF-IDF + Logistic Regression, trained normally |
| v2-bad | Must be rolled back | Same pipeline trained with a large share of labels flipped, or very few features |
| v3-good | Must be promoted | Slightly improved settings, such as n-grams or tuned C |

Dataset: a binary text classification subset. A simple reproducible choice is two categories from scikit-learn's 20 Newsgroups dataset. Replace it with your own fake-news data later. Save held-out accuracy of every version to `models/report.json`.

### 6.4 Rollout
- Argo `Rollout` with canary steps: set weight 10, pause and analyze, set weight 50, pause and analyze, then 100.
- Traffic routing through NGINX so the percentage is exact.
- Stable and canary Services both defined.

### 6.5 Analysis gates (AnalysisTemplate, Prometheus provider)
| Metric | Condition to pass | Query idea |
|---|---|---|
| Accuracy of canary | at or above a threshold you choose (for example 0.85) | rate of correct predictions divided by rate of all labeled predictions, for the canary pods |
| p95 latency of canary | below a threshold (for example 300 ms) | `histogram_quantile(0.95, ...)` |
| Error rate of canary | below 2% | 5xx rate divided by total rate |

Rules:
- Handle the "no data yet" case so an empty result is not treated as a pass.
- Set failure limits so one noisy sample does not trigger a rollback, but a sustained failure does.
- Identify canary pods using the `rollouts-pod-template-hash` label (via `podTemplateHashValue` arguments), exposed through the ServiceMonitor `podTargetLabels` setting.

### 6.6 CI (GitHub Actions)
- On push and pull request: install deps, run ruff, run pytest, train and check model quality, build the Docker image, and on `main` push it to ghcr.io tagged with the commit SHA.
- `test_model_quality.py` fails if a model's held-out accuracy is below a minimum. This is the offline gate. The Argo analysis is the online gate.

---

## 7. Execution Plan (step by step)

Do the phases in order. Do not start a phase until the previous one's acceptance check passes.

### Phase 0: Prerequisites
Install Docker (running), kubectl, kind, Helm, Python 3.11, Git, make, and the Argo Rollouts kubectl plugin. Create the GitHub repo. Machine needs about 8 GB RAM free.
**Check:** `docker ps`, `kubectl version --client`, `kind version`, `helm version` all work.

### Phase 1: Model and API
1. Write `training/train.py` to produce v1, v2-bad and v3-good, and write `models/report.json` with each version's accuracy.
2. Write the FastAPI app with the endpoints in 6.1 and metrics in 6.2.
3. Write tests.
**Check:** `pytest` passes. `report.json` shows v2-bad clearly below v1 and v3-good at or above v1. The API runs locally and `/metrics` shows counters after a few requests.

### Phase 2: Container
1. Write the Dockerfile (slim Python base, non-root user, health check).
2. Build images for each model version, or one image with the model chosen by `MODEL_PATH`.
**Check:** `docker run` serves `/predict` and `/healthz`.

### Phase 3: Cluster and platform
1. Create the kind cluster with ingress port mappings (`k8s/kind-config.yaml`).
2. Install ingress-nginx using the kind-specific manifest from its official docs.
3. Install Argo Rollouts into its own namespace.
4. Install kube-prometheus-stack with Helm into a `monitoring` namespace.
**Check:** All pods in `ingress-nginx`, `argo-rollouts` and `monitoring` are Running.

### Phase 4: Deploy v1 as stable
1. Load the image into kind (`kind load docker-image`).
2. Apply namespace, Services, Ingress, ServiceMonitor, then the Rollout with v1.
3. Port-forward or use the ingress to reach the API.
**Check:** `kubectl argo rollouts get rollout canaryml` shows Healthy. Prometheus shows the app target as UP. `replay.py` gets responses.

### Phase 5: Analysis and canary
1. Write `analysis-template.yaml` using the three gates.
2. Add steps and analysis to the Rollout.
3. Validate manifests with kubeconform and a server-side dry run.
**Check:** Releasing v3-good (`kubectl argo rollouts set image ...`) goes 10, 50, 100 and ends Healthy.

### Phase 6: The rollback demo (the main proof)
1. Start `replay.py` at a steady rate.
2. Release v2-bad.
3. Watch with `kubectl argo rollouts get rollout canaryml --watch`.
4. Record the time to rollback, the failing metric and its value.
5. Screenshot the rollout view, the failed AnalysisRun, and the Grafana panel showing accuracy dropping.
**Check:** Rollout aborts, traffic returns to v1, and replay shows no failed requests on stable traffic.

### Phase 7: Grafana dashboard
Panels: traffic split by version, accuracy by version, p95 latency by version, error rate, rollout events. Export the JSON to `monitoring/grafana-dashboard.json`.

### Phase 8: CI
Write `.github/workflows/ci.yaml` per 6.6. Add the status badge to the README. Commit one deliberately failing test on a branch and screenshot the red run.

### Phase 9: Write-up
README with architecture diagram, how to run, the results table (real numbers), screenshots, and a Limitations section (simulated labels, local cluster).

### Stretch goals
- Run the whole canary demo inside GitHub Actions using a kind cluster as an end-to-end test.
- Argo CD for GitOps deploys.
- Delayed-label feedback with a database.
- Shadow deployment (mirror traffic to the new model without serving its responses).

---

## 8. Instructions for Antigravity (how to get correct code)

Give Antigravity this whole file, then add the rules below at the start of the session. If your version supports a project rules or instructions file, put them there. Otherwise paste them at the start of each session.

### 8.1 Languages and formats
| Area | Language / format |
|---|---|
| App, training, tests, traffic script | Python 3.11 |
| Kubernetes, Argo Rollouts, Helm values, GitHub Actions | YAML |
| Dockerfile | Dockerfile syntax |
| Automation | Makefile and Bash |
| Dashboard | Grafana JSON |

### 8.2 Rules to give Antigravity
```
You are helping build the CanaryML project described in canaryml-prd.md.

1. Work one phase at a time, in order. Stop at the end of each phase,
   show the output of the acceptance check, and wait for me.
2. Never rely on memory for versions, CRD fields, Helm values or install URLs.
   Open the official documentation for the exact tool version we pin
   (Argo Rollouts, ingress-nginx, kube-prometheus-stack, kind, GitHub Actions)
   and copy field names from it. Add a source link as a comment above each
   non-obvious manifest block.
3. Pin every dependency and image version. Record them in VERSIONS.md.
4. Validate before applying: run kubeconform on every manifest and
   `kubectl apply --dry-run=server`. Fix errors instead of guessing.
5. Run the code. Do not claim something works until you have run it and
   pasted the real output. If a command fails, show the error and diagnose it.
6. Do not invent numbers. Accuracy, latency and rollback times must come from
   actual runs and be written to files I can see.
7. Keep the code simple and readable. No extra frameworks beyond the PRD stack.
8. Ask me before adding any tool that is not in the PRD.
9. Never commit secrets or tokens. Use GitHub Actions secrets and environment
   variables.
10. After each phase, update README.md with what was built and how to run it.
```

### 8.3 Prompt to start each phase
Use this template, filling in the phase number:
```
Do Phase N of canaryml-prd.md only. First list the files you will create or
change and the official docs pages you will check. Then implement it, run the
acceptance check, and show me the real output. Stop after that.
```

### 8.4 Phase-specific prompts
- **Phase 1:** "Write training/train.py to produce three scikit-learn pipelines (v1 baseline, v2-bad with deliberately degraded training, v3-good with improved settings) on a binary text subset of 20 Newsgroups. Save each model with joblib and write held-out accuracy to models/report.json. Then write the FastAPI app and tests exactly as specified in section 6."
- **Phase 3:** "Using the current official kind, ingress-nginx, Argo Rollouts and kube-prometheus-stack docs, give me the exact commands to set up the cluster. Put them in a Makefile target `make up`. Show every command's output."
- **Phase 5:** "Write the AnalysisTemplate with the Prometheus provider for the three gates in section 6.5. Use the podTemplateHashValue argument for the canary. Handle empty query results safely. Check the field names against the Argo Rollouts docs for the pinned version."
- **Phase 6:** "Run the rollback demo. Start replay.py, release v2-bad, and capture timestamps, the failing AnalysisRun and the metric value. Save everything under docs/results/."

### 8.5 If Antigravity gets something wrong
- Paste the exact error and ask for a diagnosis that cites the official docs.
- If a CRD field is rejected, ask it to run `kubectl explain` on that resource and fix the manifest from the output.
- If it produces something you do not understand, ask it to explain the block line by line before you accept it. You need to explain this in interviews.

---

## 9. Demo Script (for README video or interview)
1. Show the dashboard with v1 serving 100%.
2. Start replay traffic.
3. Release v2-bad. Show the 10% canary appear.
4. Show accuracy dropping on the canary panel.
5. Show the automatic rollback and the stable version still at 100% with no errors.
6. Release v3-good and show promotion to 100%.

---

## 10. Deliverables
- Public GitHub repo with the structure in section 5
- README with results table, screenshots and limitations
- Screenshot of the automatic rollback with the failing metric
- Grafana dashboard JSON
- Green CI badge and one screenshot of a failed CI run
- 2-minute screen recording of the demo

### Results table template (fill with real data only)
| Version | Held-out accuracy | Canary accuracy | p95 latency | Outcome | Time to decision |
|---|---|---|---|---|---|
| v1 | | | | stable | |
| v2-bad | | | | rolled back | |
| v3-good | | | | promoted | |

### Resume / LinkedIn line (fill the brackets with real numbers)
> Built a progressive-delivery pipeline for an ML model on Kubernetes (Argo Rollouts, Prometheus, GitHub Actions): 10% canary releases gated on accuracy, latency and error rate, with automatic rollback in [N seconds] on a degraded model.

### Interview talking points
- Why offline accuracy is not enough, and what the online gate adds
- Why the labels are simulated here and how delayed labels would change the design
- Why a single bad sample should not trigger a rollback (failure limits)
- Canary vs blue-green vs shadow deployment, and when you would pick each

---

## 11. Risks and Mitigations
| Risk | Mitigation |
|---|---|
| Laptop too slow for the full stack | Reduce Prometheus resources; use fewer replicas; close other apps |
| Metrics not appearing in Prometheus | Check ServiceMonitor labels match the Helm release; check the target page in Prometheus |
| Analysis passes on empty data | Explicitly treat no data as failure or inconclusive |
| Canary label not found in queries | Confirm `podTargetLabels` and the sanitized label name `rollouts_pod_template_hash` |
| Versions drift and manifests break | Pin versions in VERSIONS.md and copy fields from matching docs |
| Port conflicts with ingress on the laptop | Change the host ports in the kind config |

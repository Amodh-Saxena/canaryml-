# Project History and Context

This file serves as a checkpoint summarizing the progress and context for the CanaryML project. 

## Completed Phases

### Phase 0: Prerequisites Setup
- **Tooling:** Created `scripts/install-tools.sh` to download and install pinned CLI binaries into `./bin/` (kubectl, kind, helm, argo-rollouts, kubeconform).
- **Documentation:** Created `VERSIONS.md` containing strict version pins and their official source URLs.
- **Python Setup:** Initialized a Python 3.11 virtual environment (`.venv`) and pinned runtime and development dependencies in `requirements.txt` and `requirements-dev.txt`.
- **Ignore Rules:** Set up `.gitignore` to avoid tracking binaries, `__pycache__`, the virtual environment, and `.joblib` model artifacts.

### Phase 1: ML Model and API Implementation
- **Model Training:** 
  - Explored scikit-learn models on the `20newsgroups` dataset. 
  - Implemented `training/train.py` to generate three `scikit-learn` Pipeline models (TF-IDF + LogisticRegression) using the 'rec.autos' and 'sci.med' categories:
    - `v1` (baseline)
    - `v2-bad` (degraded accuracy via limited features and flipped labels)
    - `v3-good` (improved accuracy via n-grams and tuned C)
  - Trained models are output to `models/` as `.joblib` files, alongside a `report.json` tracking their baseline offline accuracy.
- **FastAPI Application:** 
  - Implemented the API in `app/main.py` offering `/predict`, `/healthz`, and `/metrics` endpoints.
  - Implemented fault injection (via `FAULT_LATENCY_MS` and `FAULT_ERROR_RATE` environment variables) via middleware.
  - Defined Prometheus metrics in `app/metrics.py` for tracking `http_requests_total`, `http_request_duration_seconds`, and `model_predictions_total`.
- **Testing:** 
  - Implemented API tests in `tests/test_api.py`.
  - Implemented model offline gate tests in `tests/test_model_quality.py`.
  - Verified that all unit tests and quality gates pass successfully on the generated models.

### Phase 2: Containerization and CI (Completed)
- Created `Dockerfile` and `.dockerignore` for serving the model via FastAPI.
- Configured `.github/workflows/ci.yml` to lint, run tests, and build/push the Docker image to GitHub Container Registry.
- Added `bin/`, `.git/`, `models/report.json` to `.dockerignore` (keeps ~300 MB of CLI binaries out of the build context).
- **Verified 2026-10-05 (Docker Engine 29.8.1):** `docker build -t canaryml:v1 .` succeeds; container reaches `(healthy)`; `/healthz` -> ok; `/predict` returns correct labels; `/metrics` exposes `http_requests_total` and `model_predictions_total`; `v1`, `v2-bad`, `v3-good` all load via `MODEL_PATH`.
- Note: the image has no default `MODEL_PATH`; it must be passed with `-e MODEL_PATH=/app/models/<version>.joblib -e MODEL_VERSION=<version>`.
- CI has successfully run on GitHub Actions and the image `ghcr.io/amodh-saxena/canaryml` is pushed to the container registry.

## Next Steps
- **Phase 3:** Cluster and platform setup (create the `kind` cluster with ingress mappings, install ingress-nginx, Argo Rollouts, and kube-prometheus-stack).

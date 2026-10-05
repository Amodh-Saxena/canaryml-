# Pinned Versions

Every version below was looked up from an official source on 2026-10-05 and is the
version this project is built and tested against. Do not change one without
re-checking the compatibility notes.

## Local tooling (Phase 0)

| Tool | Version | Source used to pick it | How it is installed |
|---|---|---|---|
| kubectl | v1.35.9 | https://dl.k8s.io/release/stable-1.35.txt | `scripts/install-tools.sh` -> `bin/` (sha256 verified) |
| kind | v0.33.0 | https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0 | `scripts/install-tools.sh` -> `bin/` |
| Helm | v4.3.0 | https://github.com/helm/helm/releases/tag/v4.3.0 | `scripts/install-tools.sh` -> `bin/` |
| kubectl-argo-rollouts | v1.10.0 | https://github.com/argoproj/argo-rollouts/releases/tag/v1.10.0 | `scripts/install-tools.sh` -> `bin/` |
| kubeconform | v0.8.0 | https://github.com/yannh/kubeconform/releases/tag/v0.8.0 | `scripts/install-tools.sh` -> `bin/` |
| GNU make | 4.4.1 (ezwinports) | `winget show ezwinports.make` | `winget install --id ezwinports.make --version 4.4.1` |
| Python | 3.11.9 | https://www.python.org/downloads/ (last 3.11 release with a Windows installer) | `winget install --id Python.Python.3.11 --version 3.11.9 --scope user` |
| Git (incl. Git Bash) | 2.53.0.windows.2 | already installed | n/a |
| Docker Desktop | _filled in after install_ | https://docs.docker.com/desktop/setup/install/windows-install/ | manual (admin) |

## Cluster components (used from Phase 3)

| Component | Version | Source |
|---|---|---|
| Kubernetes node image | `kindest/node:v1.35.8@sha256:07b2536e30b803ed61d1677a79df6115f798ce64c80f9e22f6ed45afd09323c0` | kind v0.33.0 release notes (pre-built images list) |
| ingress-nginx controller | controller-v1.15.1 (Helm chart 4.15.1) | https://github.com/kubernetes/ingress-nginx#supported-versions-table |
| Argo Rollouts controller | v1.10.0 | https://github.com/argoproj/argo-rollouts/releases/tag/v1.10.0 |
| kube-prometheus-stack chart | 91.9.0 (prometheus-operator v0.94.1) | https://github.com/prometheus-community/helm-charts/releases/tag/kube-prometheus-stack-91.9.0 |

## Compatibility notes (why Kubernetes 1.35, not the newest 1.37)

- **ingress-nginx v1.15.1** is tested on Kubernetes 1.31 to 1.35 only (README supported-versions table).
- **Argo Rollouts v1.10.0** e2e matrix tests 1.32 to 1.35, with 1.35 marked `latest`
  (`.github/workflows/testing.yaml` at tag v1.10.0).
- **Helm 4.3.x** supports Kubernetes 1.34 to 1.37 (https://helm.sh/docs/topics/version_skew/).
- **kube-prometheus-stack 91.9.0** has `kubeVersion: ">=1.25.0-0"` in its Chart.yaml.
- kubectl v1.35.9 is within the supported +/-1 minor skew of the 1.35.8 node image.

> **ingress-nginx is retired.** Per its README and the Kubernetes blog
> (https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/), maintenance ended in
> March 2026 with no further releases or security fixes. Artifacts remain available.
> It is kept here because the PRD specifies it, and this is a local, non-production demo.

> **Python patch version:** python.org publishes no Windows installers for 3.11.10 and later
> (security-only releases are source-only). Local dev uses 3.11.9. The Docker image will pin
> its own 3.11.x patch tag, chosen in Phase 2.

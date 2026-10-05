# CanaryML

Zero-downtime ML model rollout on Kubernetes with automated canary analysis
(Argo Rollouts + ingress-nginx + Prometheus). See [canaryml-prd.md](canaryml-prd.md).

## Status

| Phase | Status |
|---|---|
| 0. Prerequisites | CLI tools, Python 3.11.9 and make installed and verified; waiting on Docker Desktop |
| 1. Model and API | completed |
| 2. Container and CI | Dockerfile and CI workflow written; not yet verified (needs Docker) |
| 3. Cluster | not started |

## Phase 0: Prerequisites

All pinned versions and the reasons for them are in [VERSIONS.md](VERSIONS.md).
The cluster targets **Kubernetes 1.35** because that is the newest version supported
by both ingress-nginx v1.15.1 and Argo Rollouts v1.10.0.

### 1. Docker Desktop (manual, needs admin)

Windows 11 Home needs WSL2. In an **admin** PowerShell:

```powershell
wsl --install --no-distribution   # then reboot
```

Then install Docker Desktop from https://docs.docker.com/desktop/setup/install/windows-install/
(WSL2 backend). Low on C: space? Move the disk image in
Docker Desktop > Settings > Resources > Advanced > Disk image location (e.g. `D:\DockerData`).

### 2. CLI tools (kubectl, kind, helm, kubectl-argo-rollouts, kubeconform)

Downloaded into `./bin` with SHA-256 verification (runs in Git Bash):

```powershell
& "C:\Program Files\Git\bin\bash.exe" scripts/install-tools.sh
$env:PATH = "$PWD\bin;$env:PATH"   # per shell session
```

### 3. Python 3.11 and make

```powershell
winget install --id Python.Python.3.11 --version 3.11.9 --scope user
winget install --id ezwinports.make --version 4.4.1
```

### Check

```powershell
docker ps
kubectl version --client
kind version
helm version
kubectl argo rollouts version
kubeconform -v
make --version
py -3.11 --version
```

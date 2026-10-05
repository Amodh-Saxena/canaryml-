#!/usr/bin/env bash
# Downloads pinned CLI tools into ./bin and verifies each SHA-256 checksum.
# Versions must match VERSIONS.md. Windows amd64 only (run from Git Bash).
set -euo pipefail

KUBECTL_VERSION=v1.35.9
KIND_VERSION=v0.33.0
HELM_VERSION=v4.3.0
ARGO_ROLLOUTS_VERSION=v1.10.0
KUBECONFORM_VERSION=v0.8.0

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$ROOT/bin"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$BIN"

# verify <file> <expected-sha256>
verify() {
  local actual
  actual="$(sha256sum "$1" | awk '{print $1}')"
  if [[ "$actual" != "$2" ]]; then
    echo "CHECKSUM MISMATCH for $1: expected $2, got $actual" >&2
    exit 1
  fi
  echo "  sha256 OK $(basename "$1")"
}

fetch() { curl -fsSL --retry 3 -o "$2" "$1"; }

# kubectl - https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/
echo "kubectl $KUBECTL_VERSION"
fetch "https://dl.k8s.io/release/$KUBECTL_VERSION/bin/windows/amd64/kubectl.exe" "$TMP/kubectl.exe"
verify "$TMP/kubectl.exe" "$(curl -fsSL "https://dl.k8s.io/release/$KUBECTL_VERSION/bin/windows/amd64/kubectl.exe.sha256" | tr -d '[:space:]')"
mv "$TMP/kubectl.exe" "$BIN/kubectl.exe"

# kind - https://kind.sigs.k8s.io/docs/user/quick-start/#installing-from-release-binaries
echo "kind $KIND_VERSION"
fetch "https://kind.sigs.k8s.io/dl/$KIND_VERSION/kind-windows-amd64" "$TMP/kind.exe"
verify "$TMP/kind.exe" "$(curl -fsSL "https://kind.sigs.k8s.io/dl/$KIND_VERSION/kind-windows-amd64.sha256sum" | awk '{print $1}')"
mv "$TMP/kind.exe" "$BIN/kind.exe"

# helm - https://helm.sh/docs/intro/install/#from-the-binary-releases
echo "helm $HELM_VERSION"
fetch "https://get.helm.sh/helm-$HELM_VERSION-windows-amd64.zip" "$TMP/helm.zip"
verify "$TMP/helm.zip" "$(curl -fsSL "https://get.helm.sh/helm-$HELM_VERSION-windows-amd64.zip.sha256sum" | awk '{print $1}')"
unzip -q -o "$TMP/helm.zip" -d "$TMP/helm"
mv "$TMP/helm/windows-amd64/helm.exe" "$BIN/helm.exe"

# Argo Rollouts kubectl plugin - https://argo-rollouts.readthedocs.io/en/stable/installation/#kubectl-plugin-installation
echo "kubectl-argo-rollouts $ARGO_ROLLOUTS_VERSION"
ARGO_URL="https://github.com/argoproj/argo-rollouts/releases/download/$ARGO_ROLLOUTS_VERSION"
fetch "$ARGO_URL/kubectl-argo-rollouts-windows-amd64" "$TMP/kubectl-argo-rollouts.exe"
verify "$TMP/kubectl-argo-rollouts.exe" "$(curl -fsSL "$ARGO_URL/argo-rollouts-checksums.txt" | awk '$2 ~ /kubectl-argo-rollouts-windows-amd64$/ {print $1}')"
mv "$TMP/kubectl-argo-rollouts.exe" "$BIN/kubectl-argo-rollouts.exe"

# kubeconform - https://github.com/yannh/kubeconform#installation
echo "kubeconform $KUBECONFORM_VERSION"
KC_URL="https://github.com/yannh/kubeconform/releases/download/$KUBECONFORM_VERSION"
fetch "$KC_URL/kubeconform-windows-amd64.zip" "$TMP/kubeconform.zip"
verify "$TMP/kubeconform.zip" "$(curl -fsSL "$KC_URL/CHECKSUMS" | awk '$2 ~ /kubeconform-windows-amd64.zip$/ {print $1}')"
unzip -q -o "$TMP/kubeconform.zip" -d "$TMP/kubeconform"
mv "$TMP/kubeconform/kubeconform.exe" "$BIN/kubeconform.exe"

echo "All tools installed in $BIN"

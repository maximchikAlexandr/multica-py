#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TAG="${TAG:-}"
VERSION="${VERSION:-}"
COMMIT="${COMMIT:-}"
RELEASE_ID="${RELEASE_ID:-}"
BINARY="${BINARY:-}"
ASSET_NAME="${ASSET_NAME:-}"
SHA256="${SHA256:-}"
OS="${OS:-linux}"
ARCH="${ARCH:-amd64}"
VERSION_OUTPUT="${VERSION_OUTPUT:-}"
OUTPUT_DIR="${OUTPUT_DIR:-${ROOT}/artifacts/upstream-upgrades/manual}"

if [[ -z "${TAG}" ]]; then
  echo "upstream-upgrade: set TAG (for example TAG=v0.4.3)" >&2
  exit 2
fi

if [[ -z "${VERSION}" ]]; then
  VERSION="${TAG#v}"
fi

required=(COMMIT RELEASE_ID BINARY ASSET_NAME SHA256 VERSION_OUTPUT)
for name in "${required[@]}"; do
  if [[ -z "${!name}" ]]; then
    echo "upstream-upgrade: set ${name} for verified collect provenance" >&2
    exit 2
  fi
done

exec uv run python "${ROOT}/scripts/upstream_contract.py" --repo-root "${ROOT}" upgrade \
  --tag "${TAG}" \
  --version "${VERSION}" \
  --commit "${COMMIT}" \
  --release-id "${RELEASE_ID}" \
  --binary "${BINARY}" \
  --asset-name "${ASSET_NAME}" \
  --sha256 "${SHA256}" \
  --os "${OS}" \
  --arch "${ARCH}" \
  --version-output "${VERSION_OUTPUT}" \
  --output-dir "${OUTPUT_DIR}"

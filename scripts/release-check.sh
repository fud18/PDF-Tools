#!/usr/bin/env bash

# ==============================================================================
# PDF Tools Release Validation
#
# Purpose:
#     Validate source quality, repository state, production deployment, and
#     release metadata before creating a version tag.
#
# Author:
#     Cory Funk 2026
# ==============================================================================

set -Eeuo pipefail

REPOSITORY_DIRECTORY="${PDFTOOLS_REPOSITORY_DIRECTORY:-/opt/PDF-Tools}"
EXPECTED_BRANCH="${PDFTOOLS_EXPECTED_BRANCH:-main}"
EXPECTED_VERSION="${PDFTOOLS_EXPECTED_VERSION:-0.5.0}"
RELEASE_TAG="${PDFTOOLS_RELEASE_TAG:-v${EXPECTED_VERSION}}"

cd "${REPOSITORY_DIRECTORY}"

echo "==================== PDF Tools Release Check ===================="
echo "Repository: ${REPOSITORY_DIRECTORY}"
echo "Expected branch: ${EXPECTED_BRANCH}"
echo "Expected version: ${EXPECTED_VERSION}"
echo "Release tag: ${RELEASE_TAG}"
echo

current_branch="$(git branch --show-current)"

if [[ "${current_branch}" != "${EXPECTED_BRANCH}" ]]; then
    echo "ERROR: Current branch is ${current_branch}; expected ${EXPECTED_BRANCH}."
    exit 1
fi

echo "Branch check passed."

git fetch --prune --tags origin

if [[ -n "$(git status --porcelain)" ]]; then
    echo "ERROR: The working tree is not clean."
    git status --short
    exit 1
fi

echo "Working-tree check passed."

local_commit="$(git rev-parse HEAD)"
remote_commit="$(git rev-parse "origin/${EXPECTED_BRANCH}")"

if [[ "${local_commit}" != "${remote_commit}" ]]; then
    echo "ERROR: Local HEAD does not match origin/${EXPECTED_BRANCH}."
    echo "Local:  ${local_commit}"
    echo "Remote: ${remote_commit}"
    exit 1
fi

echo "Remote synchronization check passed."

if git rev-parse "${RELEASE_TAG}" >/dev/null 2>&1; then
    echo "ERROR: Release tag ${RELEASE_TAG} already exists."
    exit 1
fi

echo "Tag availability check passed."

configured_version="$(
    python3 - <<'PY'
from app.core.configuration import get_settings

print(get_settings().app_version)
PY
)"

package_version="$(
    python3 - <<'PY'
import tomllib
from pathlib import Path

document = tomllib.loads(
    Path("pyproject.toml").read_text(encoding="utf-8")
)

print(document["project"]["version"])
PY
)"

constant_version="$(
    python3 - <<'PY'
from app.core.version import APP_VERSION

print(APP_VERSION)
PY
)"

for discovered_version in \
    "${configured_version}" \
    "${package_version}" \
    "${constant_version}"
do
    if [[ "${discovered_version}" != "${EXPECTED_VERSION}" ]]; then
        echo "ERROR: Found version ${discovered_version}; expected ${EXPECTED_VERSION}."
        exit 1
    fi
done

echo "Version consistency check passed."

echo
echo "Running Ruff..."
ruff check .

echo
echo "Running Black..."
black --check .

echo
echo "Running mypy..."
mypy app

echo
echo "Running pytest..."
pytest

echo
echo "Running production smoke tests..."
PDFTOOLS_EXPECTED_VERSION="${EXPECTED_VERSION}" \
    ./scripts/smoke-test.sh

echo
echo "Release validation passed."
echo "The repository is ready to tag as ${RELEASE_TAG}."
echo "================================================================"

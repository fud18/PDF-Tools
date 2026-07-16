#!/usr/bin/env bash

# ==============================================================================
# PDF Tools Production Smoke Test
#
# Purpose:
#     Validate the deployed PDF Tools service through its public HTTPS endpoint.
#
# Author:
#     Cory Funk 2026
# ==============================================================================

set -Eeuo pipefail

BASE_URL="${PDFTOOLS_BASE_URL:-https://pdf-tools.rstechwiz.net}"
EXPECTED_VERSION="${PDFTOOLS_EXPECTED_VERSION:-0.5.0}"

temporary_directory="$(mktemp -d)"

cleanup() {
    rm -rf "${temporary_directory}"
}

trap cleanup EXIT

echo "==================== PDF Tools Smoke Test ===================="
echo "Base URL: ${BASE_URL}"
echo "Expected version: ${EXPECTED_VERSION}"
echo

health_file="${temporary_directory}/health.json"
openapi_file="${temporary_directory}/openapi.json"

echo "Checking health endpoint..."

curl \
    --silent \
    --show-error \
    --fail-with-body \
    "${BASE_URL}/v1/health" \
    --output "${health_file}"

python3 - "${health_file}" "${EXPECTED_VERSION}" <<'PY'
import json
import sys
from pathlib import Path

health_path = Path(sys.argv[1])
expected_version = sys.argv[2]

payload = json.loads(health_path.read_text(encoding="utf-8"))

assert payload["success"] is True
assert payload["version"] == expected_version
assert payload["data"]["version"] == expected_version
assert payload["data"]["status"] == "healthy"
assert payload["request_id"]

print("Health endpoint passed.")
PY

echo
echo "Checking OpenAPI document..."

curl \
    --silent \
    --show-error \
    --fail-with-body \
    "${BASE_URL}/openapi.json" \
    --output "${openapi_file}"

python3 - "${openapi_file}" "${EXPECTED_VERSION}" <<'PY'
import json
import sys
from pathlib import Path

openapi_path = Path(sys.argv[1])
expected_version = sys.argv[2]

schema = json.loads(openapi_path.read_text(encoding="utf-8"))

assert schema["info"]["version"] == expected_version
assert "PDFToolsAPIKey" in schema["components"]["securitySchemes"]

required_paths = {
    "/v1/health",
    "/v1/health/details",
    "/v1/metrics",
    "/v1/pdf/inspect",
    "/v1/pdf/fill",
    "/v1/pdf/merge",
}

missing_paths = sorted(required_paths - set(schema["paths"]))

assert not missing_paths, f"Missing OpenAPI paths: {missing_paths}"

print("OpenAPI validation passed.")
PY

echo
echo "Checking Swagger UI..."

swagger_status="$(
    curl \
        --silent \
        --output /dev/null \
        --write-out '%{http_code}' \
        "${BASE_URL}/docs"
)"

if [[ "${swagger_status}" != "200" ]]; then
    echo "Swagger UI returned HTTP ${swagger_status}."
    exit 1
fi

echo "Swagger UI passed."

echo
echo "Checking authentication enforcement..."

authentication_status="$(
    curl \
        --silent \
        --output "${temporary_directory}/authentication.json" \
        --write-out '%{http_code}' \
        "${BASE_URL}/v1/metrics"
)"

if [[ "${authentication_status}" != "401" ]]; then
    echo "Metrics endpoint returned HTTP ${authentication_status}; expected 401."
    cat "${temporary_directory}/authentication.json"
    exit 1
fi

python3 - "${temporary_directory}/authentication.json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert payload["success"] is False
assert payload["error"]["code"] == "PDFT-1101"

print("Authentication enforcement passed.")
PY

echo
echo "All production smoke tests passed."
echo "=============================================================="

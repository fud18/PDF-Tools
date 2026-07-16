#!/usr/bin/env bash

# ==============================================================================
# PDF Tools Deployment Script
#
# Purpose:
#     Deploys the tracked PDF Tools source files from the infrastructure
#     repository into the production runtime directory.
#
# Author:
#     Cory Funk 2026
# ==============================================================================

set -Eeuo pipefail

SOURCE_DIRECTORY="/opt/PDF-Tools"
DEPLOY_DIRECTORY="/opt/pdf-tools"
SERVICE_NAME="pdf-tools"
SERVICE_USER="pdftools"
SERVICE_GROUP="pdftools"

echo "Deploying PDF Tools..."

install -d \
    -o "${SERVICE_USER}" \
    -g "${SERVICE_GROUP}" \
    -m 0750 \
    "${DEPLOY_DIRECTORY}"

rsync -a --delete \
    --exclude='.git/' \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='tests/' \
    --exclude='docs/' \
    "${SOURCE_DIRECTORY}/app/" \
    "${DEPLOY_DIRECTORY}/app/"

install -m 0644 \
    "${SOURCE_DIRECTORY}/requirements.txt" \
    "${DEPLOY_DIRECTORY}/requirements.txt"

chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${DEPLOY_DIRECTORY}"

if [[ ! -x "${DEPLOY_DIRECTORY}/venv/bin/python" ]]; then
    python3 -m venv "${DEPLOY_DIRECTORY}/venv"
fi

"${DEPLOY_DIRECTORY}/venv/bin/python" -m pip install --upgrade \
    pip \
    setuptools \
    wheel

"${DEPLOY_DIRECTORY}/venv/bin/pip" install \
    -r "${DEPLOY_DIRECTORY}/requirements.txt"

chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${DEPLOY_DIRECTORY}"

if systemctl is-enabled "${SERVICE_NAME}.service" >/dev/null 2>&1; then
    systemctl restart "${SERVICE_NAME}.service"
else
    echo "WARNING: ${SERVICE_NAME}.service is not enabled; skipping restart."
fi

echo "PDF Tools deployment completed."

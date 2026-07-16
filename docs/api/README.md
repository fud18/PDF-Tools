# API Documentation

## Overview

PDF Tools exposes a versioned REST API under `/v1`.

Current endpoints:

- GET /v1/health
- POST /v1/pdf/inspect
- POST /v1/pdf/fill

Interactive documentation:

- /docs
- /redoc
- /openapi.json

All endpoints requiring access must include a valid `X-API-Key` header.

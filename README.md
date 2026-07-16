# PDF Tools

> A secure, self-hosted REST API for PDF processing and document automation.

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-v0.3.1-orange.svg)

## Overview

PDF Tools is a production-oriented REST API designed to provide secure, reusable, and high-performance PDF processing services for internal automation projects.

Unlike desktop PDF applications or cloud-based PDF services, PDF Tools is intended to run entirely within your own infrastructure, allowing documents containing sensitive information to be processed without leaving your environment.

Typical consumers include:

- Google Apps Script
- PowerShell automation
- Python applications
- Internal web applications
- Server-side workflows

## Design Goals

- Secure by default
- No document persistence
- No field-value logging
- Stateless REST API
- Versioned endpoints
- Modular architecture
- Production-ready documentation
- Fully testable

## Current Features

### Health Monitoring

`GET /v1/health`

### PDF Inspection

`POST /v1/pdf/inspect`

Returns:

- Page count
- Metadata
- Form field names
- Field types
- Signature fields
- Encryption status

### PDF Form Filling

`POST /v1/pdf/fill`

Supports:

- AcroForms
- Text fields
- Checkboxes
- Optional field validation
- Optional flattening
- In-memory processing

### OpenAPI

- `/docs`
- `/redoc`
- `/openapi.json`

## Planned Features

- Template Engine
- PDF Merge
- PDF Split
- Rotate
- Watermark
- Compression
- Image to PDF
- Office to PDF (LibreOffice)

## Security

PDF Tools is designed to:

- Process PDFs entirely in memory whenever possible.
- Never persist uploaded or generated documents.
- Never log document contents or field values.
- Require API key authentication.
- Operate behind HTTPS.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.13+ |
| API | FastAPI |
| ASGI | Uvicorn |
| PDF | pypdf |
| Reverse Proxy | Nginx |
| Service | systemd |
| Testing | pytest |
| Formatting | Black |
| Linting | Ruff |
| Type Checking | mypy |

## Installation

```bash
git clone git@github.com:fud18/PDF-Tools.git
cd PDF-Tools

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Run:

```bash
uvicorn app.main:app --reload
```

## Development

```bash
pytest
black .
ruff check .
mypy .
```

## Roadmap

- v0.3.x Repository Foundation
- v0.4.x Production Platform
- v0.5.x Template Engine
- v0.6.x PDF Merge
- v0.7.x PDF Split
- v0.8.x Watermarks
- v0.9.x Compression
- v1.0.0 Production Release

## License

Released under the MIT License.

## Author

**Cory Funk**

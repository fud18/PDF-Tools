# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.
This project adheres to Semantic Versioning.

## [0.5.0] - 2026-07-16

### Added
- Authenticated `POST /v1/pdf/merge` endpoint
- `pdf.merge` client permission
- Ordered merging of repeated multipart `files` fields
- Optional sanitized `output_name` form field
- Configurable merge file-count and aggregate request-size limits
- In-memory PDF merging without intentional document persistence
- Preservation of page dimensions and rotation
- Standard PDF Tools error responses for merge failures
- OpenAPI documentation for binary merge responses
- Unit and integration coverage for merge ordering, dimensions, rotation, authentication, authorization, limits, filenames, and validation

### Changed
- Updated application and package metadata to version 0.5.0
- Updated release and smoke-test defaults for v0.5.0

## [0.4.0] - 2026-07-16

### Added
- Standard success and error response envelopes
- Stable `PDFT-xxxx` error-code catalog
- Request ID propagation and response headers
- Centralized HTTP, validation, and application exception handling
- Authenticated Prometheus-compatible metrics endpoint
- Multiprocess metrics aggregation for Uvicorn workers
- Request totals, duration histograms, byte counters, and in-progress gauges
- Enhanced Swagger UI and OpenAPI documentation
- API key authorization support in Swagger UI
- Reusable documented error responses and schema examples
- Integration tests for platform behavior and OpenAPI generation
- Production smoke-test and release-validation scripts

### Changed
- Standardized JSON responses across existing API endpoints
- Updated project and application metadata to version 0.4.0
- Improved deployment to use the standalone repository
- Improved systemd deployment and automatic service restart
- Consolidated test and development-tool configuration

### Removed
- Obsolete duplicate middleware implementations
- Tracked Python bytecode and cache artifacts

## [0.3.1] - 2026-07-16

### Added
- Standalone repository foundation
- Professional README
- MIT License
- Initial changelog
- Standard .gitignore

## [0.3.0] - 2026-07-16

### Added
- PDF inspection endpoint
- PDF form filling
- Optional AcroForm flattening
- API key authentication
- OpenAPI documentation
- Unit tests

## [0.2.0]

### Added
- Authentication middleware
- Structured logging
- Production middleware

## [0.1.0]

### Added
- Initial FastAPI framework

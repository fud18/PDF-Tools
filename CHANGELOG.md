# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.
This project adheres to Semantic Versioning.

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

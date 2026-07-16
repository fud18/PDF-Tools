# Architecture

PDF Tools uses a layered architecture:

- API layer (FastAPI routes)
- Service layer (business logic)
- Models (request/response schemas)
- Core (configuration, authentication, logging)

Deployment consists of FastAPI behind Nginx with systemd managing the service.

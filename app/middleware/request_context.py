from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_id import HEADER_NAME, generate_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = generate_request_id()
        response = await call_next(request)
        response.headers[HEADER_NAME] = request.state.request_id
        return response

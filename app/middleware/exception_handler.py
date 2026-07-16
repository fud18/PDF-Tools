from fastapi.responses import JSONResponse

from app.core.exceptions import PDFToolsException
from app.core.responses import fail


async def pdf_tools_exception_handler(request, exc: PDFToolsException):
    payload = fail(
        request.state.request_id,
        exc.code,
        exc.message,
        exc.details,
    )
    return JSONResponse(status_code=400, content=payload.model_dump(mode="json"))

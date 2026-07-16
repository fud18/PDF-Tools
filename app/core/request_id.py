from uuid import uuid4

HEADER_NAME = "X-Request-ID"


def generate_request_id() -> str:
    return str(uuid4())

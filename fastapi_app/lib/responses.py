from typing import Any, Mapping
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask

class JResponse(JSONResponse):
    content = {
        "status" : "ok",
        "message" : "",
        "body" : None
    }
    
    def __init__(self, message: str = "Success", body: Any | None = None, status_code: int = 200, headers: Mapping[str, str] | None = None, media_type: str | None = None, background: BackgroundTask | None = None) -> None:
        self._message(message)
        self._body(body)
        super().__init__(self.content, status_code, headers, media_type, background)
    
    def _message(self, message: str) -> None:
        self.content["message"] = message
    
    def _body(self, body: Any):
        self.content["body"] = body


class Created(JResponse):
    def __init__(self, message: str = "Created", body: Any | None = None, status_code: int = 201, headers: Mapping[str, str] | None = None, media_type: str | None = None, background: BackgroundTask | None = None) -> None:
        super().__init__(message, status_code, headers, media_type, background)
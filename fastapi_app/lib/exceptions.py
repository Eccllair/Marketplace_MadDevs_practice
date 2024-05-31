from typing import Any, Mapping
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask

class ResponseException(JSONResponse):
    content: dict ={
        "status" : "fail",
        "message" : ""
    }
    
    def __init__(self, message: str = "Bad Request", status_code: int = 400, headers: Mapping[str, str] | None = None, media_type: str | None = None, background: BackgroundTask | None = None) -> None:
        self._message(message)
        super().__init__(self.content, status_code, headers, media_type, background)
    
    def _message(self, message: str) -> None:
        self.content["message"] = message


class Forbidden(ResponseException):
    def __init__(self, message: str = "forbidden", status_code: int = 403, headers: Mapping[str, str] | None = None, media_type: str | None = None, background: BackgroundTask | None = None) -> None:
        super().__init__(message, status_code, headers, media_type, background)

class NotFound(ResponseException):
    def __init__(self, message: str = "Not Found", status_code: int = 404, headers: Mapping[str, str] | None = None, media_type: str | None = None, background: BackgroundTask | None = None) -> None:
        super().__init__(message, status_code, headers, media_type, background)

class NotAcceptable(ResponseException):
    def __init__(self, message: str = "Not Acceptable", status_code: int = 406, headers: Mapping[str, str] | None = None, media_type: str | None = None, background: BackgroundTask | None = None) -> None:
        super().__init__(message, status_code, headers, media_type, background)


#TODO
class CustomError(Exception):
    def __init__(self):
        self.message = ""
    
    def __str__(self):
        return self.message
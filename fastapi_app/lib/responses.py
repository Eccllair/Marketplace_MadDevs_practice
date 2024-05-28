from fastapi.responses import JSONResponse

response_ok = JSONResponse(
    content={
        "status" : "ok",
        "message" : "success.",
        "body" : None
    }
)
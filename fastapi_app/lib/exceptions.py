from fastapi.responses import JSONResponse

response_not_enough_rights = JSONResponse(
            content={
                "status" : "fail",
                "message" : "not enough rights"
            },
            status_code=403
        )


#TODO
class CustomError(Exception):
    def __init__(self):
        self.message = ""
    
    def __str__(self):
        return self.message
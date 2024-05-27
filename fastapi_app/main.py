import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from .routers.user_router import user_router, auth_router

load_dotenv()
LOG_PATH = os.getenv('LOG_PATH')
tags_metadata = [
    {
        "name": "auth",
        "description": "authorization.",
    },
    {
        "name": "users",
        "description": "actions with the user.",
        # "externalDocs": {
        #     "description": "Items external docs",
        #     "url": "https://fastapi.tiangolo.com/",
        # },
    },
]

app = FastAPI(openapi_tags=tags_metadata)

logging.basicConfig(filename=LOG_PATH, level=logging.INFO)

app.include_router(
    router=auth_router,
    prefix="/api/v1",
    tags=["auth"]
)

app.include_router(
    router=user_router,
    prefix="/api/v1/users",
    tags=["users"]
)

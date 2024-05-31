import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from .routers.user_router import user_router, auth_router
from .routers.shop_router import shop_router

load_dotenv()
LOG_PATH = os.getenv('LOG_PATH')
tags_metadata = [
    {
        "name": "auth",
        "description": "authorization.",
    },
    {
        "name": "users",
        "description": "actions with user.",
        # "externalDocs": {
        #     "description": "Items external docs",
        #     "url": "https://fastapi.tiangolo.com/",
        # },
    },
    {
        "name": "shops",
        "description": "actions with shop.",
    },
]
API_VERSION="/api/v1"

app = FastAPI(openapi_tags=tags_metadata)

logging.basicConfig(filename=LOG_PATH, level=logging.INFO)

app.include_router(
    router=auth_router,
    prefix=f"{API_VERSION}",
    tags=["auth"]
)

app.include_router(
    router=user_router,
    prefix=f"{API_VERSION}/users",
    tags=["users"]
)

app.include_router(
    router=shop_router,
    prefix=f"{API_VERSION}/shops",
    tags=["shops"]
)

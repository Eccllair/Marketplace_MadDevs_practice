from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD  = os.getenv('POSTGRES_PASSWORD')
POSTGRES_SERVER  = os.getenv('POSTGRES_SERVER')
POSTGRES_PORT  = os.getenv('POSTGRES_PORT')
POSTGRES_DB  = os.getenv('POSTGRES_DB')

SQLALCHEMY_DATABASE_URL=f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}'

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

async_session_maker: sessionmaker[Session] = sessionmaker(engine, class_=AsyncSession, expire_on_commit=True)
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
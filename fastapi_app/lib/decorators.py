from typing import Annotated

from fastapi import HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.engine import Result
from sqlalchemy import select

from secure import check_jwt, create_jwt, decode_jwt
from fastapi import Cookie

from ..models import User
from ..database import get_async_session

def jwt_confirmed(func: function, access_token: Annotated[str | None, Cookie()] = None, refresh_token: Annotated[str | None, Cookie()] = None, session: Session = Depends(get_async_session)):
    async def inner(access_token = access_token, refresh_token = refresh_token, session = session):
        ## проверка токенов пользователя
        if await check_jwt(access_token):
            return func()
        else:
            if await check_jwt(refresh_token):
                response: Response = Response()
                user = decode_jwt(refresh_token)
                user_from_db: Result = await session.execute(select(User).where(User.login == user.login))
                db_user: User = user_from_db.scalar_one_or_none()
                if not user: raise HTTPException(status_code=401, detail="Unauthorized")
                else:
                    response.set_cookie(await create_jwt(db_user, is_refresh=False))
                return func(response=response)
            else:
                raise HTTPException(status_code=401, detail="Unauthorized")
    return inner
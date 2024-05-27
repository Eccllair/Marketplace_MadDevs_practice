import logging
from datetime import date
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Cookie
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.engine import Result

from ..lib.pydantic_models import pd_signup_user, pd_user
from ..lib.secure import create_jwt, check_jwt, check_email
from ..models import User
from ..database import get_async_session

user_router = APIRouter()
auth_router = APIRouter()

# TODO @is_superuser
# TODO @is_admin
# TODO @is_selfuser


###authorization
@auth_router.post("/signin")
async def signin(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Session = Depends(get_async_session)
    ):
    #TODO проверка верификации почты
    access_token = None
    refresh_token = None
    
    # и проверка данных входа
    user_from_db: Result = await session.execute(select(User).where(User.login == form_data.username))
    user: User = user_from_db.mappings().one_or_none()
    if not user: raise HTTPException(status_code=400, detail="Incorrect username or password")
    if form_data.password != user.pwd_hash: raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # создание новых токенов
    access_token = await create_jwt(user, is_refresh=False)
    refresh_token = await create_jwt(user, is_refresh=True)
            
    ## формирование ответа
    response = JSONResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })
    response.set_cookie("access_token", access_token)
    response.set_cookie("refresh_token", refresh_token)
    return response


@auth_router.post("/signup")
async def signup(user: pd_signup_user, session: Session = Depends(get_async_session)):
    if not check_email(user.mail): raise HTTPException(status_code=400, detail="wrong email addres")
    try:
        await session.execute(insert(User).values(login = user.login, mail=user.mail, pwd_hash=user.pwd_hash))
        await session.commit()
    except IntegrityError as e:
        logging.error(f'user registration error:\n{e._message}')
        raise HTTPException(status_code=400, detail="user already exists")
    return Response(status_code=201)


@auth_router.post("/make-coffe")
async def make_coffe():
    raise HTTPException(status_code=418)


###actions with user
@user_router.get("/")
async def get_users(session: Session = Depends(get_async_session)):
    users: Result = await session.execute(select(User.id, User.login, User.name, User.surname, User.patronymic, User.mail, User.avatar_img))
    return users.mappings().all()

#TODO @is_selfuser
@user_router.patch("/")
async def edit_user(user: pd_user, session: Session = Depends(get_async_session)):
    values = user.model_dump(exclude_none=True)
    await session.execute(update(User).where(User.login == user.login).values(values))
    await session.commit()
    return Response(status_code=200)


@user_router.delete("/{id}")
async def delete_user(id:int, session: Session = Depends(get_async_session)):
    await session.execute(delete(User).where(User.id == id))
    await session.commit()
    return 200


@user_router.get("/{login}")
async def get_user(login:str, session: Session = Depends(get_async_session)):
    user_from_db: Result = await session.execute(select(User.id, User.login, User.name, User.surname, User.patronymic, User.mail, User.avatar_img).where(User.login == login))
    return user_from_db.mappings().one()

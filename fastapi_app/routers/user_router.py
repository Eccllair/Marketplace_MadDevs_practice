import logging
from datetime import datetime
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

from ..lib.pydantic_models import pd_signup_user, pd_user, pd_user_role, roles
from ..lib.secure import create_jwt, check_jwt, check_email, get_current_user, bcrypt_context
from ..lib.exceptions import Forbidden, NotFound, ResponseException
from ..lib.responses import JResponse, Created
from ..models import User
from ..database import get_async_session

user_router = APIRouter()
auth_router = APIRouter()


###authorization
@auth_router.post("/signin")
async def signin(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Session = Depends(get_async_session)
    ):
    #TODO проверка верификации почты
    access_token = None
    refresh_token = None
    
    # проверка данных входа
    user_from_db: Result = await session.execute(select(User).where(User.login == form_data.username))
    user: User = user_from_db.scalar_one()
    exception = ResponseException(message="Incorrect username or password")
    if not user: return exception
    if not bcrypt_context.verify(form_data.password, user.pwd_hash): return exception
    
    # создание новых токенов
    access_token = await create_jwt(user, is_refresh=False)
    refresh_token = await create_jwt(user, is_refresh=True)
            
    ## формирование ответа
    response = JSONResponse({
        "status" : "ok",
        "message" : "Authorization passed. New tokens created",
        "body" : None,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })
    response.set_cookie("access_token", access_token)
    response.set_cookie("refresh_token", refresh_token)
    return response


@auth_router.post("/signup")
async def signup(user: pd_signup_user, session: Session = Depends(get_async_session)):
    if not check_email(user.mail):
        return ResponseException(message="user already exists")
    try:
        await session.execute(insert(User).values(login = user.login, mail=user.mail, pwd_hash=bcrypt_context.hash(user.password)))
        await session.commit()
    except IntegrityError as e:
        logging.error(f'user registration error:\n{e._message}')
        return ResponseException(message="user already exists")
    return Created(message="The user has been successfully created.")


@auth_router.post("/make-coffe")
async def make_coffe():
    return JSONResponse(
        content={
            "status" : "fail",
            "message" : "The server is deployed on a teapot. Please refer to the coffee maker"
        },
        status_code=418
    )


###actions with user
@user_router.get("/")
async def get_users(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    users: Result = await session.execute(select(User.id, User.login, User.name, User.surname, User.patronymic, User.mail, User.avatar_img))
    return JResponse([dict(user) for user in users.mappings().all()])


@user_router.patch("/")
async def edit_user(user: pd_user, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if user.id != cur_user.id:
        return Forbidden(message="you can only change yourself")
    values: dict = user.model_dump(exclude_none=True)
    try:
        await session.execute(update(User).where(User.id == user.id).values(values))
        await session.commit()
        new_user_data: Result = await session.execute(select(User.id, User.login, User.name, User.surname, User.patronymic, User.mail, User.avatar_img).where(User.id == user.id))
        return JResponse(body=dict(new_user_data.mappings().one()))
    except NoResultFound as e:
        logging.error(f'404 PATCH user not found:\n{e._message}')
        return NotFound(message=f"user with id [{user.id}] not found.")


@user_router.delete("/{id}")
async def delete_user(id:int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if not (cur_user.is_admin or cur_user.is_superuser): 
        return Forbidden()
    try:
        await session.execute(delete(User).where(User.id == id))
        await session.commit()
        return JResponse()
    except NoResultFound as e:
        logging.error(f'404 DELETE user not found:\n{e._message}')
        return NotFound(message=f"user with id [{id}] not found.")


@user_router.get("/{id}")
async def get_user(id:int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    try:
        user_from_db: Result = await session.execute(select(User.id, User.login, User.name, User.surname, User.patronymic, User.mail, User.avatar_img).where(User.id == id))
        return user_from_db.mappings().one()
    except NoResultFound as e:
        logging.error(f'404 GET user not found:\n{e._message}')
        return NotFound(message=f"user with id [{id}] not found.")


@user_router.post("/set-role")
async def set_role(new_user_role: pd_user_role, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if not cur_user.is_superuser:
        return Forbidden()
    match new_user_role.role:
        case roles.user:
            await session.execute(update(User).values(is_admin=False, is_superuser=False).where(User.id == new_user_role.id))
        case roles.admin:
            await session.execute(update(User).values(is_admin=True, is_superuser=False).where(User.id == new_user_role.id))
        case roles.superuser:
            await session.execute(update(User).values(is_admin=True, is_superuser=True).where(User.id == new_user_role.id))
    await session.commit()
    return JResponse(message="user role updated")


@user_router.post("/block")
async def block(id: int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if not (cur_user.is_superuser or cur_user.is_admin):
        return Forbidden()
    await session.execute(update(User).values(is_blocked=True, blocking_datetime=datetime.now()).where(User.id == id))
    await session.commit()
    return JResponse(message="user is blocked")

@user_router.post("/unblock")
async def unblock(id: int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if not (cur_user.is_superuser or cur_user.is_admin): 
        return Forbidden()
    await session.execute(update(User).values(is_blocked=False, blocking_datetime=None).where(User.id == id))
    await session.commit()
    return JResponse(message="user is unblocked")
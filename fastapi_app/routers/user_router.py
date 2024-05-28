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
from ..lib.exceptions import response_not_enough_rights
from ..lib.responses import response_ok
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
    exception = JSONResponse(
            content={
                "status" : "fail",
                "message" : "Incorrect username or password"
            },
            status_code=400
        )
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
        return JSONResponse(
            content={
                "status" : "fail",
                "message" : "wrong email addres"
            },
            status_code=400
        )
    try:
        await session.execute(insert(User).values(login = user.login, mail=user.mail, pwd_hash=bcrypt_context.hash(user.password)))
        await session.commit()
    except IntegrityError as e:
        logging.error(f'user registration error:\n{e._message}')
        return JSONResponse(
            content={
                "status" : "fail",
                "message" : "user already exists"
            },
            status_code=400
        )
    return JSONResponse(
        content={
            "status" : "ok",
            "message" : "The user has been successfully created.",
            "body" : None
        },
        status_code=201
    )


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
    return JSONResponse(
        content={
            "status" : "ok",
            "message" : "success.",
            "body" : [dict(user) for user in users.mappings().all()]
        },
        status_code=200
    )


@user_router.patch("/")
async def edit_user(user: pd_user, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if user.id != cur_user.id:
        return JSONResponse(
            content={
                "status" : "fail",
                "message" : "you can only change yourself."
            },
            status_code=403
        )
    values = user.model_dump(exclude_none=True)
    try:
        await session.execute(update(User).where(User.id == user.id).values(values))
        await session.commit()
        new_user_data: Result = await session.execute(select(User.id, User.login, User.name, User.surname, User.patronymic, User.mail, User.avatar_img).where(User.id == user.id))
        return JSONResponse({
            "status": "ok",
            "message": "success.",
            "body": dict(new_user_data.mappings().one())
        })
    except NoResultFound as e:
        logging.error(f'user not found:\n{e._message}')
        return JSONResponse(
            content={
                "status" : "fail",
                "message" : f"user with id [{user.id}] not found."
            },
            status_code=404
        )


@user_router.delete("/{id}")
async def delete_user(id:int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if not (cur_user.is_admin or cur_user.is_superuser): 
        return response_not_enough_rights
    try:
        await session.execute(delete(User).where(User.id == id))
        await session.commit()
        return response_ok
    except NoResultFound as e:
        logging.error(f'user not found:\n{e._message}')
        return JSONResponse(
            content={
                "status" : "fail",
                "message" : f"user with id [{id}] not found."
            },
            status_code=404
        )


@user_router.get("/{id}")
async def get_user(id:int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    try:
        user_from_db: Result = await session.execute(select(User.id, User.login, User.name, User.surname, User.patronymic, User.mail, User.avatar_img).where(User.id == id))
        return user_from_db.mappings().one()
    except NoResultFound as e:
        logging.error(f'user not found:\n{e._message}')
        return JSONResponse(
            content={
                "status" : "fail",
                "message" : f"user with id [{id}] not found."
            },
            status_code=404
        )


@user_router.post("/set-role")
async def set_role(new_user_role: pd_user_role, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if not cur_user.is_superuser:
        return response_not_enough_rights
    match new_user_role.role:
        case roles.user:
            await session.execute(update(User).values(is_admin=False, is_superuser=False).where(User.id == new_user_role.id))
        case roles.admin:
            await session.execute(update(User).values(is_admin=True, is_superuser=False).where(User.id == new_user_role.id))
        case roles.superuser:
            await session.execute(update(User).values(is_admin=True, is_superuser=True).where(User.id == new_user_role.id))
    await session.commit()
    return JSONResponse(
            content={
                "status" : "ok",
                "message" : "user role updated",
                "body" : None
            },
            status_code=200
        )


@user_router.post("/block")
async def block(id: int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if not (cur_user.is_superuser or cur_user.is_admin):
        return response_not_enough_rights
    await session.execute(update(User).values(is_blocked=True, blocking_datetime=datetime.now()).where(User.id == id))
    await session.commit()
    return JSONResponse(
            content={
                "status" : "ok",
                "message" : "user is blocked"
            },
            status_code=200
        )

@user_router.post("/unblock")
async def unblock(id: int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    if not (cur_user.is_superuser or cur_user.is_admin): 
        return response_not_enough_rights
    await session.execute(update(User).values(is_blocked=False, blocking_datetime=None).where(User.id == id))
    await session.commit()
    return JSONResponse(
            content={
                "status" : "ok",
                "message" : "user is unblocked"
            },
            status_code=200
        )
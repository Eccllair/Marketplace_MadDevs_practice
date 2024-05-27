### sys import
import jwt
import re
import os
from dotenv import load_dotenv

### std import
import random
import string
from datetime import datetime, timedelta
from typing import Annotated

### web import
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import HTTPException
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.engine import Result
from sqlalchemy import select, insert

### custom import
from .pydantic_models import pd_jwt
from ..models import JWT, User, VerifyCode
from ..database import async_session_maker

### глобальные переменные
load_dotenv()

JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')
email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b' #регулярное выражение проверки почты

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") #указание типа аутентификации для FastAPI

### функции
## работа с почтой пользователя
def check_email(email: str) -> bool:
    if(re.fullmatch(email_regex, email)): return True
    else: return False


async def generate_code(user: User, session: Session = async_session_maker()):
    # при использовании в редких случаях стоит обрабатывать sqlalchemy.exc.IntegrityError
    gen_type = random.randint(0,9)
    code = ""
    match gen_type:
        case 0:
            a = ''.join(random.choices(string.digits, k=3))
            code = a + a[0] + ''.join(random.choices(string.digits, k=2))
        case 1:
            a = ''.join(random.choices(string.digits, k=3))
            code = a + str(random.randint(0,9)) + a[1:3]
        case 2:
            a = ''.join(random.choices(string.digits, k=3))
            code = a + a[0] + str(random.randint(0,9)) + a[2]
        case 3:
            a = ''.join(random.choices(string.digits, k=3))
            code = a + a[3::-1]
        case _:
            code = ''.join(random.choices(string.digits, k=6))
    await session.execute(insert(VerifyCode).values(user_id = user.id, code = code, date_of_creation = datetime.nox()))
    await session.commit()
    return code


#TODO сделать отправку сообщений на почту, через почтовый микросервис
async def send_mait_to(message: str, target_email: str):
    pass


## работа с токенами доступа пользователя
async def create_jwt(user: User, is_refresh = False, session: Session = async_session_maker()) -> str:
    # при использовании стоит обрабатывать sqlalchemy.exc.NoResultFound (в редких случаях sqlalchemy.exc.IntegrityError)
    jwt_dict = dict(pd_jwt(login=user.login, is_refresh=is_refresh))
    token = jwt.encode(jwt_dict, JWT_SECRET, algorithm=JWT_ALGORITHM)
    await session.execute(insert(JWT).values(user = user.id, token=token))
    await session.commit()
    return token


def decode_jwt(jwt_str: str) -> pd_jwt:
    jwt_dict = jwt.decode(jwt_str, JWT_SECRET, [JWT_ALGORITHM])
    token = pd_jwt(
        login=jwt_dict["login"],
        is_refresh=jwt_dict["is_refresh"],
        creation_date=jwt_dict["creation_date"],
        expiration_date=jwt_dict["expiration_date"]
    )
    return token


async def check_jwt(jwt_str: str, session: Session = async_session_maker()) -> bool:
    # при использовании стоит обрабатывать sqlalchemy.exc.NoResultFound
    token_from_db: Result = await session.execute(select(JWT).where(JWT.token == jwt_str))
    token_exists = bool(token_from_db.scalar_one_or_none())
    if token_exists:
        token = decode_jwt(jwt_str)
        if datetime(token.expiration_date) < datetime.now(): return False
        else: return True
    else: return False


#работа напрямую с аудетнификацией
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Session = async_session_maker()) -> User:
    exception = HTTPException(status_code=401, detail="Invalid authentication credentials", headers={"WWW-Authenticate": "Bearer"})
    
    if not await check_jwt(token): raise exception
    
    user: pd_jwt = decode_jwt(token)
    if not user: raise exception
    
    user_from_bd: Result = await session.execute(select(User).where(User.login == user.login))
    bd_user: User = user_from_bd.scalar_one_or_none()
    if not bd_user: raise exception
    
    return bd_user

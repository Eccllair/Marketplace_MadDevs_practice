
#sys imort
import os
from dotenv import load_dotenv

#std import
from datetime import datetime, timedelta
from enum import Enum

#web import
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

#custom import
from ..database import async_session_maker
from ..models import User


load_dotenv()

JWT_ACCESS_LIFETIME = int(os.getenv('JWT_ACCESS_LIFETIME'))
JWT_REFRESH_LIFETIME = int(os.getenv('JWT_REFRESH_LIFETIME'))

class roles(Enum):
    user = 0
    admin = 1
    superuser = 2

class pd_signup_user(BaseModel):
    login: str
    mail: str
    password: str
    
class pd_user_role(BaseModel):
    id: int
    role: roles

class pd_user(BaseModel):
    id: int
    login: str | None
    name: str | None
    surname: str | None
    patronymic: str | None
    mail: str | None
    avatar_img: str | None
    
class pd_jwt(BaseModel):
    login: str
    creation_date: str
    expiration_date: str
    is_refresh: bool
        
    def __init__(
            self,
            login: str,
            is_refresh: bool,
            creation_date: datetime | None = None,
            expiration_date: datetime | None = None
        ):
        if creation_date: new_creation_date = creation_date
        else: new_creation_date = datetime.now()
        if expiration_date: new_expiration_date = expiration_date
        else: new_expiration_date = datetime.now() + timedelta(days=JWT_REFRESH_LIFETIME if is_refresh else JWT_ACCESS_LIFETIME)
        super().__init__(login=login, is_refresh=is_refresh, creation_date=str(new_creation_date), expiration_date=str(new_expiration_date))
    
    async def get_user(self, session: Session = async_session_maker()) -> User:
        return await session.execute(select(User).where(User.login == self.login))
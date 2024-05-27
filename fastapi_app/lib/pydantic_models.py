
import os
from dotenv import load_dotenv

from datetime import datetime, timedelta

from pydantic import BaseModel


load_dotenv()

JWT_ACCESS_LIFETIME = int(os.getenv('JWT_ACCESS_LIFETIME'))
JWT_REFRESH_LIFETIME = int(os.getenv('JWT_REFRESH_LIFETIME'))


class pd_signup_user(BaseModel):
    login: str
    mail: str
    pwd_hash: str

class pd_user(BaseModel):
    login: str
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
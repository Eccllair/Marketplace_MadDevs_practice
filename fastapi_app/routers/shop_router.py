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
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.engine import Result
from sqlalchemy.engine.row import RowMapping

from ..lib.pydantic_models import pd_shop, pd_shop_edit, pd_position, pd_position_edit
from ..lib.secure import create_jwt, check_jwt, check_email, get_current_user, bcrypt_context
from ..lib.exceptions import NotFound, Forbidden, NotAcceptable
from ..lib.responses import JResponse
from ..models import User, Shop, ShopImage, ShopAndUser, Position
from ..database import get_async_session

shop_router = APIRouter()


@shop_router.get("/")
async def get_shops(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    """get all shops"""
    shops_result: Result = await session.execute(select(Shop.id, Shop.name, Shop.avatar_img, Shop.description, Shop.is_confirmed).where(Shop.is_deleted == False))
    shops: list[RowMapping] = shops_result.mappings().all()
    
    shops_response = []
    for shop in shops:
        shop_images_result: Result = await session.execute(select(ShopImage.src).where(ShopImage.shop_id == shop.id))
        shop_images: list = shop_images_result.scalars().all()
        shops_response.append(
            {
                "shop" : dict(shop),
                "images" : shop_images
            }
        )
    
    return JResponse(body=shops_response)


@shop_router.get("/{id}")
async def get_shop(id:int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    try:
        shop_result: Result = await session.execute(select(Shop.id, Shop.name, Shop.avatar_img, Shop.description, Shop.is_confirmed, Shop.is_deleted).where(Shop.id == id))
        shop: RowMapping = shop_result.mappings().one()
    except NoResultFound as e:
        logging.error(f"404 GET shop error:\n{e._message()}")
        return NotFound(message=f"shop with id [{id}] does not exists")
    if shop.is_deleted == True: return NotAcceptable(message="shop has been deleted")
    
    shop_images_result: Result = await session.execute(select(ShopImage.src).where(ShopImage.shop_id == shop.id))
    shop_images: list = shop_images_result.scalars().all()
    
    shop_d = dict(shop)
    shop_d.pop("is_deleted")
    body = {
        "shop" : shop_d,
        "images" : shop_images
    }
    return JResponse(body=body)


@shop_router.post("/")
async def create_shop(shop: pd_shop, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    shop_d: dict = shop.model_dump(exclude_none=True)
    await session.execute(insert(Shop).values(owner_id=cur_user.id, **shop_d))
    await session.commit()
    return JResponse()


@shop_router.patch("/")
async def edit_shop(shop: pd_shop_edit, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    #проверка входных данных
    try:
        shop_db_r: Result = await session.execute(select(Shop).where(Shop.id == shop.id))
        shop_db: Shop = shop_db_r.scalar_one()
    except NoResultFound as e:
        logging.error(f"PATCH shop error: {e._message()}")
        return NotFound(message=f"shop with id [{shop.id}] does not exists")
    if shop_db.owner_id != cur_user.id: return Forbidden(message="only shop owner can change shop")
    if shop_db.is_deleted == True: return NotAcceptable(message="shop has been deleted")
    
    #редактирвние записи магазина
    values: dict = shop.model_dump(exclude_none=True, exclude={"id"})
    await session.execute(update(Shop).values(values).where(Shop.id == shop.id))
    await session.commit()
    
    #формирование ответа
    new_shop_r: Result = await session.execute(select(Shop.id, Shop.name, Shop.description, Shop.avatar_img, Shop.is_confirmed).where(Shop.id == shop.id))
    new_shop: dict = dict(new_shop_r.mappings().one())
    return JResponse(message="shop updated", body=new_shop)


@shop_router.delete("/")
async def delete_shop(shop_id: int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    #проверка входных данных
    try:
        shop_db_r: Result = await session.execute(select(Shop).where(Shop.id == shop_id))
        shop_db: Shop = shop_db_r.scalar_one()
    except NoResultFound as e:
        logging.error(f"DELETE shop error: {e._message()}")
        return NotFound(message=f"shop with id [{shop_id}] does not exists")
    if shop_db.owner_id != cur_user.id: return Forbidden(message="only shop owner can delete shop")
    if shop_db.is_deleted == True: return NotAcceptable(message="shop already deleted")
    
    #удаление магазина
    await session.execute(update(Shop).values(is_deleted=True).where(Shop.id == shop_id))
    await session.commit()


@shop_router.post("/images")
async def send_images(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    #TODO
    pass


@shop_router.delete("/images")
async def delete_images(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    #TODO
    pass


@shop_router.get("/positions")
async def get_job_titles(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    """returns all positions created by the current user"""
    positions_r: Result = await session.execute(
        select(
            Position.name,
            Position.can_add_staff,
            Position.can_change_staff,
            Position.can_delete_staff,
            Position.can_add_product,
            Position.can_change_product,
            Position.can_delete_product
        )
        .where(Position.creator_id == cur_user.id)
    )
    return JResponse(body=[dict(position) for position in positions_r.mappings().all()])
    


@shop_router.get("/positions/{id}")
async def get_job_titles(id: int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    try:
        position_r: Result = await session.execute(
            select(
                Position.name,
                Position.creator_id,
                Position.can_add_staff,
                Position.can_change_staff,
                Position.can_delete_staff,
                Position.can_add_product,
                Position.can_change_product,
                Position.can_delete_product
            )
            .where(Position.id == id)
        )
    except NoResultFound as e:
        logging.error(f"GET position error: {e._message()}")
        return NotFound(message=f"position with id [{id}] does not exists")
    position: dict = position_r.mappings().one()
    if position.creator_id != cur_user.id: return Forbidden(message="you cannot get this position")
    position.pop("creator_id")
    return JResponse(body=position)


@shop_router.post("/positions")
async def create_job_title(position: pd_position, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    values = position.model_dump(exclude_none=True)
    await session.execute(
        insert(Position)
        .values(
            creator_id = cur_user.id,
            **values
        )
    )
    await session.commit()
    return JResponse()


@shop_router.patch("/positions")
async def edit_job_title(position: pd_position_edit, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    values: dict = position.model_dump(exclude_none=True, exclude={"id"})
    values["date_of_change"] = datetime.now()
    try:
        old_position_r: Result = await session.execute(select(Position).where(Position.id == position.id))
        old_position: Position = old_position_r.scalar_one()
    except NoResultFound as e:
        logging.error(f"404 edit position error: {e._message()}")
        return NotFound(message=f"position with id [{position.id}] does not exist")
    if old_position.creator_id != cur_user.id: return Forbidden()
    
    
    
    await session.execute(update(Position).values(values).where(Position.id == position.id))
    await session.commit()
    position_r: Result = await session.execute(
        select(
            Position.id,
            Position.name,
            Position.can_add_staff,
            Position.can_change_staff,
            Position.can_delete_staff,
            Position.can_add_product,
            Position.can_change_product,
            Position.can_delete_product
        )
        .where(Position.id == position.id)
    )
    new_position: dict = dict(position_r.mappings().one())
    return JResponse(message="position updated", body=new_position)


@shop_router.delete("/positions")
async def delete_job_title(position_id: int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    try:
        position_r: Result = await session.execute(select(Position).where(Position.id == position_id))
    except NoResultFound as e:
        logging.error(f"404 DELETE position not found: {e._message()}")
        return NotFound(message=f"position with id [{position_id}] does not exist")
    position: Position = position_r.scalar_one()
    if position.creator_id != cur_user.id: return Forbidden(message="you can delete position another owner")
    
    await session.execute(delete(Position).where(Position.id == position_id))
    await session.commit()
    return JResponse()


@shop_router.get("/staff")
async def get_staff(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    """returns all the user's staff"""
    staff_r: Result = await session.execute(
        select(
            User.id, User.login, User.name, User.surname, User.avatar_img,
            Position.id, Position.name,
            Shop.id, Shop.name
        )
        .from_statement(ShopAndUser)
        .join(User, User.id == ShopAndUser.user_id)
        .join(Shop, Shop.id == ShopAndUser.shop_id)
        .join(Position, Position.id == ShopAndUser.position_id)
        .where(Shop.owner_id == cur_user.id)
    )
    staff: list[dict] = staff_r.mappings().all()
    return JResponse(body=staff)

@shop_router.get("/shop-staff")
async def get_staff(shop_id:int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    """returns all users of the selected shop"""
    try:
        shop_r: Result = await session.execute(select(Shop).where(Shop.id == shop_id))
    except NoResultFound as e:
        logging.error(f"404 GET shop-staff, shop not found: {e._message()}")
        return NotFound(message=f"shop with id [{shop_id}] does not exist")
    shop: Shop = shop_r.scalar_one()
    if shop.owner_id != cur_user.id: return Forbidden(message="you can't get someone else's store")
    
    
    staff_r: Result = await session.execute(
        select(
            User.id, User.login, User.name, User.surname, User.avatar_img,
            Position.id, Position.name
        )
        .from_statement(ShopAndUser)
        .join(User, User.id == ShopAndUser.user_id)
        .join(Position, Position.id == ShopAndUser.position_id)
        .where(ShopAndUser.shop_id == shop_id)
    )
    staff: list[dict] = staff_r.mappings().all()
    return JResponse(body=staff)


@shop_router.get("/staff/{id}")
async def get_one_staff(id:int, cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    pass


@shop_router.post("/staff")
async def set_staff(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    pass


@shop_router.patch("/staff")
async def edit_staff(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    pass


@shop_router.delete("/staff")
async def delete_staff(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    pass


@shop_router.get("/requests")
async def get_requests_for_confirmation(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    pass


@shop_router.get("/requests")
async def get_request_for_confirmation(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    pass


@shop_router.post("/requests")
async def send_request_for_confirmation(cur_user: User = Depends(get_current_user), session: Session = Depends(get_async_session)):
    pass

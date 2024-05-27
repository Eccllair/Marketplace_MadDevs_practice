from datetime import date, datetime

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Float
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column
)


#родительский класс таблицы
class Base(DeclarativeBase):
    pass


#пользовтель
class User(Base):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    login: Mapped[str] = mapped_column(type_=String(255), unique=True, nullable=False)                              #уникальное имя пользователя
    name: Mapped[str] = mapped_column(type_=String(255), nullable=True)                                             #имя
    surname: Mapped[str] = mapped_column(type_=String(255), nullable=True)                                          #фамилия
    patronymic: Mapped[str] = mapped_column(type_=String(255), nullable=True)                                       #отчество
    mail: Mapped[str] = mapped_column(type_=String(255), unique=True, nullable=False)                               #почта для верификации
    pwd_hash: Mapped[str] = mapped_column(type_=String(255), nullable=False)                                        #хэш пароля
    avatar_img: Mapped[str] = mapped_column(type_=String(255), default="default.png", nullable=False)               #ссылка на аватар пользователя
    is_verified: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                       #почта подтверждена/не подтверждена
    is_admin: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                          #права на редактирование всех пользователей
    is_superuser: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                      #права на раздачу прав админа
    is_blocked: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                        #пользователь заблокирован / не заблокирован
    blocking_datetime: Mapped[datetime] = mapped_column(type_=DateTime(), default=None, nullable=True)              #дата и время блокировки


#коды верификации, отправленные на почту
class VerifyCode(Base):
    __tablename__ = "verifi_code"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))                                   #пользователь, который должен подтвердить код
    code: Mapped[str] = mapped_column(String(10), nullable=False)                                                   #пользователь, который должен подтвердить код
    date_of_creation: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False, default=datetime.now())    #дата и время создания
    

#JWT токены авторизации
class JWT(Base):
    __tablename__ = "jwt"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    user: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))                                      #владелец токена
    token: Mapped[str] = mapped_column(String(4096), nullable=False)                                                                #jwt строка


#магазин
class Shop(Base):
    __tablename__ = "shop"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    name: Mapped[str] = mapped_column(type_=String(255), nullable=False)                                            #название
    description: Mapped[str] = mapped_column(type_=Text(), nullable=False)                                          #описание
    is_deleted: Mapped[bool] = mapped_column(type_=Boolean(), default=False)                                        #флаг удаления записи магазина
    date_of_creation: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False, default=datetime.now())    #дата и время создания


#фотографии магазинов
class ShopImage(Base):
    __tablename__ = "shop_image"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    shop_id: Mapped[int] = mapped_column(ForeignKey(Shop.id, ondelete='CASCADE'))                                   #магазин, для которого сделано фото
    src: Mapped[str] = mapped_column(type_=String(255), nullable=False)                                             #ссылка на изображение


#позиция сотрудников магазина и права сотрудников этой позиции
class Position(Base):
    __tablename__ = "position"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    name: Mapped[str] = mapped_column(type_=String(255), nullable=False)                                            #название
    can_add_staff: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                     #возможность добавлять сотрудников магазина
    can_change_staff: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                  #возможность изменять сотрудников магазина
    can_delete_staff: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                  #возможность удалять сотрудников магазина
    can_add_product: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                   #возможность добавлять продукты магазина
    can_change_product: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                #возможность изменять продукты магазина
    can_delete_product: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                #возможность удалять продукты магазина
    date_of_creation: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False, default=datetime.now())    #дата и время создания
    date_of_change: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False)                              #дата и время изменения


#сотрудники магазина
class ShopAndUser(Base):
    __tablename__ = "shop_and_user"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"), nullable=False)                   #сотрудник магазина
    shop_id: Mapped[int] = mapped_column(ForeignKey(Shop.id, ondelete="CASCADE"), nullable=False)                   #магазин
    position_id: Mapped[int] = mapped_column(ForeignKey(Position.id, ondelete="SET NULL"), nullable=True)           #занимаемая сотрудником должность

class Brand(Base):
    __tablename__ = "brand"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete="SET NULL"), nullable=True)                   #пользователь добавивший бренд
    name: Mapped[str] = mapped_column(String(255), nullable=False)                                                  #назване
    logo_img: Mapped[str] = mapped_column(String(255), default="default.png")                                       #ссылка на логотип
    is_confirmed: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                      #бренд подтвержден / не подтвержден
    is_creator: Mapped[bool] = mapped_column(type_=Boolean(), default=False, nullable=False)                        #пользователь, добавивший бренд является создателем бренда
    confirmation_date: Mapped[date] = mapped_column(type_=Date(), default=None, nullable=True)                      #дата подтверждения бренда
    date_of_creation: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False, default=datetime.now())    #дата и время создания
    date_of_change: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False)                              #дата и время изменения


#категория продуктов
class Category(Base):
    __tablename__ = "category"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    name: Mapped[str] = mapped_column(String(255), nullable=False)                                                  #название категории


#продукты магазинов
class Product(Base):
    __tablename__ = "product"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    brand_id: Mapped[int] = mapped_column(ForeignKey(Brand.id, ondelete="SET NULL"), nullable=True)                 #бренд продукта
    category_id: Mapped[int] = mapped_column(ForeignKey(Category.id, ondelete="SET NULL"), nullable=True)           #категория, к которой относится продукт
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete="SET NULL"), nullable=True)                   #пользователь добавивший продукт

class ProductImage(Base):
    __tablename__ = "product_image"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    brand_id: Mapped[int] = mapped_column(ForeignKey(Brand.id, ondelete="SET NULL"), nullable=True)                 #продукт, для которого было сделано фото
    src: Mapped[str] = mapped_column(type_=String(255), default="default.png")                                      #ссылка на изображение
    confirmed: Mapped[bool] = mapped_column(type_=Boolean(), default=False)                                         #изображение одобрено модерацией


#запросы на подтверждение бренда
class RequestForConfirmation(Base):
    __tablename__ = "request_for_confirmation"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    brand_id: Mapped[int] = mapped_column(ForeignKey(Brand.id, ondelete="CASCADE"))                                 #какой бренд оставил запрос на подтверждение
    is_processed: Mapped[bool] = mapped_column(Boolean(), default=True)                                             #запрос в обработке / обработан
    is_rejected: Mapped[bool] = mapped_column(Boolean(), default=None, nullable=True)                               #запрос отклонен / одобрен
    date_of_creation: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False, default=datetime.now())    #дата и время создания
    date_of_change: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False)                              #дата и время изменения


#наличие продукта в магазине 
class ProductInShop(Base):
    __tablename__ = "product_in_shop"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    shop_id: Mapped[int] = mapped_column(ForeignKey(Shop.id, ondelete="CASCADE"))                                   #магазин, в котором лежит продукт
    product_id: Mapped[int] = mapped_column(ForeignKey(Product.id, ondelete="SET NULL"), nullable=True)             #продукт, который лежит в магазине
    amount: Mapped[int] = mapped_column(Integer(), default=None, nullable=True)                                   #количество продукта
    price: Mapped[float] = mapped_column(Float(), default=None, nullable=True)                                      #цена продукта
    date_of_creation: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False, default=datetime.now())    #дата и время создания


#изображения продуктов в магазине
class ProductInShopImage(Base):
    __tablename__ = "product_in_shop_image"

    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    product_in_shop: Mapped[int] = mapped_column(ForeignKey(ProductInShop.id, ondelete="CASCADE"))                  #продукт магазина, для которого было сделано фото
    src: Mapped[str] = mapped_column(String(255), default="default.png")                                            #ссылка на изображение


#корзины пользователя
class Basket(Base):
    __tablename__ = "basket"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))                                   #пользователь, которому принадлежит корзина
    is_paid: Mapped[bool] = mapped_column(type_=Boolean(), default=False)                                           #оплачено / не оплачено


#чеки оплаты
class Payment(Base):
    __tablename__ = "payment"
    
    id: Mapped[int] = mapped_column(type_=Integer(), primary_key=True, autoincrement=True)                          #уникальный идентификатор
    product_id: Mapped[int] = mapped_column(ForeignKey(Product.id, ondelete="SET NULL"), nullable=True)             #продукт, который был продан
    shop_id: Mapped[int] = mapped_column(ForeignKey(Shop.id, ondelete="SET NULL"), nullable=True)                   #магазин, в котором была совершена покупка
    basket_id: Mapped[int] = mapped_column(ForeignKey(Basket.id, ondelete="CASCADE"))                               #оплаченная корзина пользователя
    amount: Mapped[int] = mapped_column(Integer(), nullable=False)                                                  #количество товара в чеке
    total: Mapped[float] = mapped_column(type_=Float(), nullable=False)                                             #суммарная стоимость до вычета налогов
    tax: Mapped[float] = mapped_column(type_=Float(), nullable=False)                                               #НДФЛ и другие налоги
    date_of_creation: Mapped[datetime] = mapped_column(type_=DateTime(), nullable=False, default=datetime.now())    #дата и время создания


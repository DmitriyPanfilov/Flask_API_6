"""
Необходимо создать базу данных для интернет-магазина. База данных должна состоять из трёх таблиц:
товары, заказы и пользователи.
— Таблица «Товары» должна содержать информацию о доступных товарах, их описаниях и ценах.
— Таблица «Заказы» должна содержать информацию о заказах, сделанных пользователями.
— Таблица «Пользователи» должна содержать информацию о зарегистрированных пользователях магазина.
• Таблица пользователей должна содержать следующие поля: id (PRIMARY KEY), имя, фамилия, адрес электронной почты и пароль.
• Таблица заказов должна содержать следующие поля: id (PRIMARY KEY), id пользователя (FOREIGN KEY), id товара (FOREIGN KEY), дата заказа и статус заказа.
• Таблица товаров должна содержать следующие поля: id (PRIMARY KEY), название, описание и цена.

Создайте модели pydantic для получения новых данных и возврата существующих в БД для каждой из трёх таблиц.
Реализуйте CRUD операции для каждой из таблиц через создание маршрутов, REST API.
"""

from fastapi import FastAPI, HTTPException
from typing import List
from random import randint
import datetime
from datetime import datetime
from pydantic import BaseModel, Field
import databases
import sqlalchemy

DATABASE_URL = "sqlite:///mystore.db"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

app = FastAPI()


users = sqlalchemy.Table("users", metadata,
                         sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
                         sqlalchemy.Column("name", sqlalchemy.String(32)),
                         sqlalchemy.Column("surname", sqlalchemy.String(32)),
                         sqlalchemy.Column("email", sqlalchemy.String(128)),
                         sqlalchemy.Column("password", sqlalchemy.String(32)),
                         )

products = sqlalchemy.Table("products", metadata,
                            sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
                            sqlalchemy.Column("title", sqlalchemy.String(50)),
                            sqlalchemy.Column("description", sqlalchemy.String(300)),
                            sqlalchemy.Column("price", sqlalchemy.Integer)
                            )

orders = sqlalchemy.Table("orders", metadata,
                          sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
                          sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id")),
                          sqlalchemy.Column("prod_id", sqlalchemy.ForeignKey("products.id")),
                          sqlalchemy.Column("date", sqlalchemy.String),
                          sqlalchemy.Column("status", sqlalchemy.String(20))
                          )

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

class UserCreate(BaseModel):
    name: str = Field(max_length=32)
    surname: str = Field(max_length=32)
    email: str = Field(max_length=128)
    password: str = Field(min_length=3)


class UserRead(BaseModel):
    id: int
    name: str = Field(max_length=32)
    surname: str = Field(max_length=32)
    email: str = Field(max_length=128)
    password: str = Field(min_length=3)


class ProductCreate(BaseModel):
    title: str = Field(max_length=50)
    description: str = Field(max_length=300)
    price: int = Field(default=0)


class ProductRead(BaseModel):
    id: int
    title: str = Field(max_length=50)
    description: str = Field(max_length=300)
    price: int = Field(default=0)


class OrderCreate(BaseModel):
    user_id: int
    prod_id: int
    date: datetime = Field(default=datetime.now())
    status: str = Field(default="created")


class OrderRead(BaseModel):
    id: int
    user_id: int
    prod_id: int
    date: str
    status: str = Field(default="created")

@app.get("/")
def root():
    return {"Message": "Hello"}


@app.get("/fake_users/{count}")
async def create_note(count: int):
    for i in range(count):
        query = users.insert().values(name=f'user{i}', surname=f'surname{i}', email=f'mail{i}@mail.ru',
                                         password=f'qwerty{i}')
        await database.execute(query)
    return {'message': f'{count} fake users create'}


@app.get("/fake_products/{count}")
async def create_note(count: int):
    for i in range(count):
        query = products.insert().values(title=f'product {i}', description=f'all about product {i}',
                                            price=randint(1, 100000))
        await database.execute(query)
    return {'message': f'{count} fake products create'}


@app.get("/fake_orders/{count}")
async def create_note(count: int):
    for i in range(count):
        query = orders.insert().values(user_id=randint(1, 20), prod_id=randint(1, 20), status="created",
                                          date=datetime.now())
        await database.execute(query)
    return {'message': f'{count} fake orders create'}


@app.get("/users/", response_model=List[UserRead])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)


@app.get("/products/", response_model=List[ProductRead])
async def read_products():
    query = products.select()
    return await database.fetch_all(query)


@app.get("/orders/", response_model=List[OrderRead])
async def read_orders():
    query = orders.select()
    return await database.fetch_all(query)


# read one user/product/order

@app.get("/users/{user_id}", response_model=UserRead)
async def read_user(user_id: int):
    query = users.select().where(users.c.id == user_id)
    user = await database.fetch_one(query)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/products/{product_id}", response_model=ProductRead)
async def read_product(product_id: int):
    query = products.select().where(products.c.id == product_id)
    product = await database.fetch_one(query)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/orders/{order_id}", response_model=OrderRead)
async def read_order(order_id: int):
    query = orders.select().where(orders.c.id == order_id)
    order = await database.fetch_one(query)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# update user/product/order

@app.put("/users/{user_id}", response_model=UserRead)
async def update_user(user_id: int, new_user: UserCreate):
    query = users.update().where(users.c.id == user_id).values(**new_user.dict())
    await database.execute(query)
    return {**new_user.dict(), "id": user_id}


@app.put("/products/{product_id}", response_model=ProductRead)
async def update_product(product_id: int, new_product: ProductCreate):
    query = products.update().where(products.c.id == product_id).values(**new_product.dict())
    await database.execute(query)
    return {**new_product.dict(), "id": product_id}


@app.put("/orders/{order_id}", response_model=OrderRead)
async def update_order(order_id: int, new_order: OrderCreate):
    query = orders.update().where(orders.c.id == order_id).values(**new_order.dict())
    await database.execute(query)
    return {**new_order.dict(), "id": order_id}


# delete user/product/order

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {'message': 'User deleted'}


@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    query = products.delete().where(products.c.id == product_id)
    await database.execute(query)
    return {'message': 'Product deleted'}


@app.delete("/orders/{order_id}")
async def delete_order(order_id: int):
    query = orders.delete().where(orders.c.id == order_id)
    await database.execute(query)
    return {'message': 'Order deleted'}
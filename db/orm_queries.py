from typing import Any, Sequence

from sqlalchemy import select, Row, RowMapping
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Product, Base

from .models import User


async def orm_get_all_objects(model: Base, session: AsyncSession) -> Sequence[Row[Any] | RowMapping | Any]:
    query = select(model)
    result = await session.execute(query)
    objects = result.scalars().all()

    return objects


async def orm_get_product_by_vendor_code(vendor_code: int, session: AsyncSession) -> Product:
    query = select(Product).where(Product.vendor_code == vendor_code)
    result = await session.execute(query)
    product = result.scalar()

    return product


async def orm_create_product(
        name: str,
        vendor_code: int,
        price: float,
        rating: float,
        feedbacks: int,
        total_amount: int,
        session: AsyncSession
) -> None:
    try:
        obj = Product(
            name=name,
            vendor_code=vendor_code,
            price=price,
            rating=rating,
            feedbacks=feedbacks,
            total_amount=total_amount,
        )
        session.add(obj)

        await session.commit()

    except SQLAlchemyError:
        pass


async def orm_create_user(username: str, session: AsyncSession) -> None:
    try:
        user = User(username=username)

        session.add(user)

        await session.commit()
    except SQLAlchemyError:
        pass

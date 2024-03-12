import asyncio
import sqlite3
import time
from pprint import pprint
from sqlite3 import IntegrityError

import requests
import sqlalchemy
from aiogram import types, Bot, Router, F
from aiogram.filters import CommandStart, Command, or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import types

from db.models import User, Product
from keyboards.reply import reply_keyboard, reply_keyboard_delete, reply_cancel_keyboard
from keyboards.inline import get_inline_keyboard
from settings import WB_API_URL
from .state import (
    ProductState,
    NotificationState,
    save_notifications_clear_state,
    send_notifications,
    get_product_message_by_object,
    get_product_message_by_data, get_product_info_from_api
)

from db.orm_queries import (
    orm_get_product_by_vendor_code,
    orm_get_all_objects,
    orm_create_product,
    orm_create_user,
)

basic_router = Router()


@basic_router.message(CommandStart())
async def start_command_handler(message: types.Message, bot: Bot, session: AsyncSession):
    await message.answer(
        'Привет! меня зовут WildBot, '
        'я помогаю в поиске и сохранении информации '
        'о товарах на таком маркетплейсе как Wildberries',
        reply_markup=reply_keyboard
    )
    username = message.from_user.username

    await orm_create_user(username, session)


@basic_router.message(
    or_f(Command('get_product_info'), (F.text.lower() == 'получить информацию по товару 📑'))
)
async def product_info_command_handler(message: types.Message, state: FSMContext):
    await message.answer('Отправьте артикул товара с вб', reply_markup=reply_cancel_keyboard)

    await state.set_state(ProductState.vendor_code)


@basic_router.message(StateFilter('*'), Command('отмена'))
@basic_router.message(StateFilter('*'), F.text.lower() == 'отмена ❌')
async def cancel_get_info_product_handler(message: types.Message, state: FSMContext):
    if await state.get_state() is None:
        return None

    await save_notifications_clear_state(state)

    await message.answer('Действие отменено', reply_markup=reply_keyboard)


@basic_router.message(ProductState.vendor_code)
async def send_product_info(message: types.Message, state: FSMContext, session: AsyncSession):
    username = message.from_user.username
    try:
        vendor_code = int(message.text)
    except ValueError:
        await message.answer('Некорректный артикул')
        return None

    await message.answer('Подождите секунду...', reply_markup=reply_keyboard)
    try:
        api_url = WB_API_URL + str(vendor_code)
        product_info = await get_product_info_from_api(api_url)

        await orm_create_product(
            name=product_info['name'],
            vendor_code=product_info['vendor_code'],
            price=product_info['price'],
            rating=product_info['rating'],
            feedbacks=product_info['feedbacks'],
            total_amount=product_info['total_amount'],
            session=session
        )

        await state.update_data(vendor_code=message.text)

        answer = await get_product_message_by_data(product_info)
        await message.answer(str(answer), reply_markup=get_inline_keyboard(
            buttons={
                'Подписаться': f'subscribe_{vendor_code}_{username}'
            },
            sizes=(2, 2)
        ), parse_mode='HTML'
                             )

        await save_notifications_clear_state(state)
    except IndexError:
        await message.answer(
            'Товара с таким артиклом не существует',
            reply_markup=reply_cancel_keyboard
        )


@basic_router.message(or_f(Command('get_history'), F.text.lower() == 'получить информацию из бд 🗄️'))
async def get_last_5_products(message: types.Message, session: AsyncSession):
    products = await orm_get_all_objects(Product, session)

    answer = ''
    counter = 0
    if len(products) != 0:
        for product in products:
            if counter > 5:
                break
            answer += await get_product_message_by_object(product)
            if product != products[-1]:
                answer += '\n________________________________________\n\n'
            counter += 1

    else:
        answer += 'В базе данных нет ни одной записи'

    await message.answer(answer, reply_markup=reply_keyboard, parse_mode='HTML')


@basic_router.callback_query(F.data.startswith('subscribe_'))
async def subscribe_to_product(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    callback_data = callback.data.split('_')

    vendor_code = int(callback_data[-2])
    product = await orm_get_product_by_vendor_code(vendor_code, session)

    await send_notifications(callback, product, state)


@basic_router.message(or_f(
    Command('stop_notifications'),
    F.text == 'Остановить уведомления 🔔')
)
async def stop_notifications_handler(message: types.Message, state: FSMContext):
    await state.update_data(notifications_enabled=False)

    await message.answer('Уведомления успешно остановлены!', reply_markup=reply_keyboard)


@basic_router.message(F)
async def exception_handler(message: types.Message):
    await message.answer('Выберите действие')

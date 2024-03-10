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
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, Product
from keyboards.reply import reply_keyboard, reply_keyboard_delete, reply_cancel_keyboard
from keyboards.inline import get_inline_keyboard
from settings import WB_API_URL
from .state import ProductState, NotificationState, save_notifications_clear_state, send_notifications, get_product_info

basic_router = Router()


@basic_router.message(CommandStart())
async def start_command_handler(message: types.Message, bot: Bot, session: AsyncSession):
    await message.answer(
        'Привет! меня зовут WildBot, '
        'я помогаю в поиске и сохранении информации '
        'о товарах на таком маркетплейсе как Wildberries',
        reply_markup=reply_keyboard
    )
    try:
        user = User(username=message.from_user.username)

        session.add(user)

        await session.commit()
    except Exception:
        pass


@basic_router.message(
    or_f(Command('get_product_info'), (F.text == 'Получить информацию по товару'))
)
async def product_info_command_handler(message: types.Message, state: FSMContext):
    await message.answer('Отправьте артикул товара с вб', reply_markup=reply_cancel_keyboard)

    await state.set_state(ProductState.vendor_code)


@basic_router.message(StateFilter('*'), Command('отмена'))
@basic_router.message(StateFilter('*'), F.text.lower() == 'отмена')
async def cancel_get_info_product_handler(message: types.Message, state: FSMContext):
    if await state.get_state() is None:
        return None

    await save_notifications_clear_state(state)

    await message.answer('Действие отменено', reply_markup=reply_keyboard)


@basic_router.message(ProductState.vendor_code)
async def send_product_info(message: types.Message, state: FSMContext, session: AsyncSession):
    username = message.from_user.username
    vendor_code = None
    try:
        vendor_code = int(message.text)
    except ValueError:
        await message.answer('Некорректный артикул')
        return None

    await message.answer('Подождите секунду...', reply_markup=reply_keyboard)
    response = requests.get(WB_API_URL + str(vendor_code))
    try:
        products_json = response.json()['data']['products'][0]

        # pprint(products_json)

        product_name = products_json.get('name', 'Не найдено')
        product_vendor_code = products_json.get('id', 'Не найдено')
        product_price = float(products_json.get('salePriceU') / 100)
        product_rating = float(products_json.get('reviewRating', 'Не найдено'))
        product_feedbacks = products_json.get('feedbacks', 'Не найдено')

        product_amount = 0
        for i in products_json['sizes'][0]['stocks']:
            product_amount += int(i['qty'])

        await state.update_data(vendor_code=message.text)

        try:
            obj = Product(
                name=product_name,
                vendor_code=product_vendor_code,
                price=product_price,
                rating=product_rating,
                feedbacks=product_feedbacks,
                total_amount=product_amount,
            )
            session.add(obj)

            await session.commit()

        except Exception:
            pass

        await message.answer(
            'Название: ' + '"' + str(product_name) + '"' + '\n'
            + '\n'
              'Артикул: ' + str(product_vendor_code) + '\n'
            + '\n'
              'Цена: ' + str(product_price) + 'rub' + '\n'
            + '\n'
              'Рейтинг товара: ' + str(product_rating) + '('
            + str(product_feedbacks) + ' оценок)' + '\n'
            + '\n'
              'Количество на складе: ' + str(product_amount),
            reply_markup=get_inline_keyboard(
                buttons={
                    'Подписаться': f'subscribe_{product_vendor_code}_{username}'
                },
                sizes=(2, 2)
            )
        )

        await save_notifications_clear_state(state)
    except IndexError:
        await message.answer(
            'Товара с таким артиклом не существует',
            reply_markup=reply_cancel_keyboard
        )


@basic_router.message(or_f(Command('get_history'), F.text == 'Получить информацию из БД'))
async def get_last_5_products(message: types.Message, session: AsyncSession):
    user_query = select(User).where(User.username == message.from_user.username)
    user_result = await session.execute(user_query)
    user = user_result.scalar()

    product_query = select(Product)
    product_result = await session.execute(product_query)
    products = product_result.scalars().all()
    answer = ''
    counter = 0
    if len(products) != 0:
        for product in products:
            if counter > 5:
                break
            answer += await get_product_info(product)
            if product != products[-1]:
                answer += '_______________________________________________________________\n\n'
            counter += 1

    else:
        answer += 'В базе данных нет ни одной записи'

    await message.answer(answer, reply_markup=reply_keyboard)


@basic_router.callback_query(F.data.startswith('subscribe_'))
async def subscribe_to_product(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    callback_data = callback.data.split('_')

    product_query = select(Product).where(Product.vendor_code == int(callback_data[-2]))
    product_result = await session.execute(product_query)
    product = product_result.scalar()

    await send_notifications(callback, product, state)


@basic_router.message(or_f(
    Command('stop_notifications'),
    F.text == 'Остановить уведомления')
)
async def stop_notifications_handler(message: types.Message, state: FSMContext):
    await state.update_data(notifications_enabled=False)
    data = await state.get_data()
    print(data)

    await message.answer('Уведомления успешно остановлены!')


@basic_router.message(F)
async def exception_handler(message: types.Message):
    await message.answer('Выберите действие')





import asyncio
import time
from pprint import pprint
from sqlite3 import IntegrityError

import requests
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

basic_router = Router()

is_notifications_on = True


class ProductState(StatesGroup):
    vendor_code = State()


class NotificationState(StatesGroup):
    notifications_enabled = State()


@basic_router.message(CommandStart())
async def start_command_handler(message: types.Message, bot: Bot, session: AsyncSession):
    await message.answer(
        'Привет! меня зовут WildBot, '
        'я помогаю в поиске и сохранении информации '
        'о товарах на таком маркетплейсе как Wildberries',
        reply_markup=reply_keyboard
    )
    try:
        user = User(
            username=message.from_user.username
        )

        session.add(user)

        await session.commit()
    except Exception:
        pass


@basic_router.message(
    StateFilter(None),
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

    await state.clear()
    await message.answer('Действие отменено', reply_markup=reply_keyboard)


@basic_router.message(ProductState.vendor_code, F.text)
async def get_product_info(message: types.Message, state: FSMContext, session: AsyncSession):
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
        await state.clear()
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

    query = select(Product)
    result = await session.execute(query)
    products = result.scalars().all()
    reply = ''
    if len(products) != 0:
        for product in products[-5:0]:
            reply += (
                    'Название: ' + '"' + str(product.name) + '"' + '\n'
                    + '\n'
                      'Артикул: ' + str(product.vendor_code) + '\n'
                    + '\n'
                      'Цена: ' + str(product.price) + 'rub' + '\n'
                    + '\n'
                      'Рейтинг товара: ' + str(product.rating) + '('
                    + str(product.feedbacks) + ' оценок)' + '\n'
                    + '\n'
                      'Количество на складе: ' + str(product.total_amount)
                    + '\n'
            )
            if product != products[-1]:
                reply += '_______________________________________________________________\n\n'
    else:
        reply = 'В базе данных нет ни одной записи'

    await message.answer(reply, reply_markup=reply_keyboard)


@basic_router.callback_query(F.data.startswith('subscribe_'))
async def subscribe_to_product(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    callback_data = callback.data.split('_')

    product_query = select(Product).where(Product.vendor_code == int(callback_data[-2]))
    product_result = await session.execute(product_query)
    product = product_result.scalar()

    user_query = select(User).where(User.username == str(callback_data[-1]))
    user_result = await session.execute(user_query)
    user = user_result.scalar()

    if user not in product.subscribers:
        product.subscribers.append(user)
        await session.commit()

    print(product.subscribers)
    await state.set_state(NotificationState.notifications_enabled)

    while True:
        notifications_enabled = await state.get_state() == NotificationState.notifications_enabled.state
        if notifications_enabled and user in product.subscribers:
            await asyncio.sleep(10)
            await callback.message.answer(
                'Название: ' + '"' + str(product.name) + '"' + '\n'
                + '\n'
                  'Артикул: ' + str(product.vendor_code) + '\n'
                + '\n'
                  'Цена: ' + str(product.price) + 'rub' + '\n'
                + '\n'
                  'Рейтинг товара: ' + str(product.rating) + '('
                + str(product.feedbacks) + ' оценок)' + '\n'
                + '\n'
                  'Количество на складе: ' + str(product.total_amount)
                + '\n')
        else:
            break


@basic_router.message(or_f(
    Command('stop_notifications'),
    F.text == 'Остановить уведомления')
)
async def stop_notifications_handler(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(notifications_enabled=False)

    user_query = select(User).where(User.username == message.from_user.username)
    user_result = await session.execute(user_query)
    user = user_result.scalar()

    product_query = select(Product)
    product_result = await session.execute(product_query)
    products = product_result.scalars().all()
    for product in products:
        try:
            product.subscribers.remove(user)
            await session.commit()
        except ValueError:
            pass
    await state.clear()
    await message.answer('Уведомления успешно остановлены!')



@basic_router.message(F)
async def exception_handler(message: types.Message):
    await message.answer('Выберите действие')

import asyncio

import aiohttp
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery

from db.models import Product
from settings import TIME_INTERVAL

from settings import WB_API_URL


class ProductState(StatesGroup):
    vendor_code = State()


class NotificationState(StatesGroup):
    notifications_enabled = State()


async def get_product_message_by_object(obj: Product) -> str:
    return (
        f'<b>Название: </b>"{obj.name}"\n \n'
        f'<b>Артикул: </b> {obj.vendor_code}\n\n'
        f'<b>Цена: </b>{obj.price}<b>rub</b>\n\n'
        f'<b>Рейтинг товара: </b>{obj.rating}(<b>{obj.feedbacks} оценок)</b>\n\n'
        f'<b>Количество на складе: </b>{obj.total_amount}'
    )


async def get_product_message_by_data(product_data: dict) -> str:
    name = product_data['name']
    vendor_code = product_data['vendor_code']
    price = product_data['price']
    rating = product_data['rating']
    feedbacks = product_data['feedbacks']
    total_amount = product_data['total_amount']
    return (
        f'<b>Название: </b>"{name}"\n \n'
        f'<b>Артикул: </b> {vendor_code}\n\n'
        f'<b>Цена: </b>{price}<b>rub</b>\n\n'
        f'<b>Рейтинг товара: </b>{rating}(<b>{feedbacks} оценок)</b>\n\n'
        f'<b>Количество на складе: </b>{total_amount}'
    )


async def get_product_message_object(product: Product) -> str:
    return (
        f'<b>Название: </b>"{product.name}"\n \n'
        f'<b>Артикул: </b> {product.vendor_code}\n\n'
        f'<b>Цена: </b>{product.price}<b>rub</b>\n\n'
        f'<b>Рейтинг товара: </b>{product.rating}(<b>{product.feedbacks} оценок)</b>\n\n'
        f'<b>Количество на складе: </b>{product.total_amount}'
    )


async def save_notifications_clear_state(state: FSMContext):
    notifications_dict = await state.get_data()

    await state.clear()
    await state.set_state(NotificationState.notifications_enabled)
    try:
        await state.update_data(notifications_enabled=notifications_dict['notifications_enabled'])
    except KeyError:
        pass


async def send_notifications(callback: CallbackQuery, product: Product, state: FSMContext):
    await state.set_state(NotificationState.notifications_enabled)

    await state.update_data(notifications_enabled=True)
    counter = 1
    while True:
        if counter == 1:
            counter += 1
            await asyncio.sleep(TIME_INTERVAL)
            continue
        notifications_enabled = await state.get_data()
        try:
            if notifications_enabled['notifications_enabled']:
                answer = await get_product_message_object(product)
                await callback.message.answer(answer, parse_mode='HTML')
                await asyncio.sleep(TIME_INTERVAL)
            else:
                await state.clear()
                break
        except KeyError:
            await state.clear()
            break


async def get_product_info_from_api(api_url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        response = await session.get(api_url)

        data = await response.json()

        product_json = data['data']['products'][0]

        product_info = dict()
        product_info['name'] = product_json.get('name', 'Не найдено')
        product_info['vendor_code'] = product_json.get('id', 'Не найдено')
        product_info['price'] = float(product_json.get('salePriceU') / 100)
        product_info['rating'] = float(product_json.get('reviewRating', 'Не найдено'))
        product_info['feedbacks'] = product_json.get('feedbacks', 'Не найдено')

        product_amount = 0

        for i in product_json['sizes'][0]['stocks']:
            product_amount += int(i['qty'])

        product_info['total_amount'] = product_amount

    return product_info

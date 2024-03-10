import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery

from db.models import Product
from settings import TIME_INTERVAL


class ProductState(StatesGroup):
    vendor_code = State()


class NotificationState(StatesGroup):
    notifications_enabled = State()


async def get_product_info(product):
    return str(
            '<b>Название: </b>' + '"' + str(product.name) + '"' + '\n'
            + '\n'
              '<b>Артикул: </b>' + str(product.vendor_code) + '\n'
            + '\n'
              '<b>Цена: </b>' + str(product.price) + '<b>' + 'rub' + '</b>' + '\n'
            + '\n'
              '<b>Рейтинг товара: </b>' + str(product.rating) + '('
            + '<b>' + str(product.feedbacks) + ' оценок)' + '</b>' + '\n'
            + '\n'
              '<b>Количество на складе: </b>' + str(product.total_amount)
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
                print(notifications_enabled['notifications_enabled'])
                answer = await get_product_info(product)
                await callback.message.answer(answer, parse_mode='HTML')
                await asyncio.sleep(TIME_INTERVAL)
            else:
                await state.clear()
                break
        except KeyError:
            await state.clear()
            break

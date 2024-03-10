from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text='Получить информацию по товару 📑'
            ),
        ],
        [
            KeyboardButton(
                text='Получить информацию из БД 🗄️'
            ),
        ],
        [
            KeyboardButton(
                text='Остановить уведомления 🔔'
            ),
        ]
    ],
    resize_keyboard=True

)

reply_cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text='Отмена ❌'
            ),
        ],
    ],
    resize_keyboard=True
)

reply_keyboard_delete = ReplyKeyboardRemove()

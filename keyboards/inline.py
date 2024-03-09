from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


def get_inline_keyboard(*, buttons: dict[str, str], sizes: tuple):
    keyboard = InlineKeyboardBuilder()

    for text, data in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()

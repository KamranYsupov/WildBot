from aiogram.types import BotCommand

TOKEN = '<your_token>'

WB_API_URL = 'https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm='

COMMANDS_LIST = [
    BotCommand(command='get_product_info', description='Получить информацию по товару'),
    BotCommand(command='stop_notifications', description='Остановить уведомления'),
    BotCommand(command='get_history', description='Получить информацию из БД'),
]

TIME_INTERVAL = 300

from telegram import Bot
from env import TG_API_KEY, CHAT_IDS

bot = Bot(token=TG_API_KEY)


async def send_to_tg(message):
    for chat_id in CHAT_IDS:
        await bot.send_message(chat_id=chat_id, text=message)

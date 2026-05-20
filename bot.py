import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "8983129680:AAHOBTUA_wt4BJLckxqg-FR2hKcdv7iIX78"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🎬 KinoKashf ga xush kelibsiz!\n\n"
        "Kino nomini yozing!"
    )

@dp.message()
async def handle(message: types.Message):
    await message.answer(f"🔍 {message.text} — tez orada kinolar qo'shiladi!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging
import sys
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.formatting import Bold, as_list, as_marked_section
from aiogram import F
from token_data import TOKEN
from recipes_handler import router

bot=aiogram.Bot(TOKEN)
dp = Dispatcher()
dp.include_router(router)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    knopki = [
        [
            types.KeyboardButton(text="Поддерживаемые команды"),
            types.KeyboardButton(text="Функционал бота"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=knopki,
        resize_keyboard=True,
    )
    await message.answer(f"Привет! Я шефбот, повар-помощник. Ознакомьтесь с информацией обо мне через функциональные кнопки снизу", reply_markup=keyboard)

@dp.message(F.text.lower() == "поддерживаемые команды")
async def commands(message: types.Message):
    response = as_list(
        as_marked_section(
            Bold("Команды:"),
            "'/category_search_random (число)' - вызов списка всех категорий с указанием числа рецептов\n"
            "/start - начало работы",
        ),
    )
    await message.answer(
        **response.as_kwargs()
    )

@dp.message(F.text.lower() == "функционал бота")
async def description(message: types.Message):
    response = as_list(
        as_marked_section(
            Bold("Функционал бота:"),
            "Бот соединён с небольшой базой рецептов блюд, разделённых на категории. "
                "Может предоставить указанное (либо максимально доступное) количество "
                "случайных рецептов по выбранной пользователем категории блюд",
        ),
    )
    await message.answer(
        **response.as_kwargs()
    )

async def main() -> None:
   bot = Bot(TOKEN)
   await dp.start_polling(bot)

if __name__ == "__main__":
   logging.basicConfig(level=logging.INFO, stream=sys.stdout)
   asyncio.run(main())
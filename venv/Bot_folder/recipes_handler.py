import aiohttp
import asyncio
import random

from googletrans import Translator
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.formatting import Bold, as_list, as_marked_section
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
translator = Translator()

recipes_for_display=[]

class searched_number(StatesGroup):
   await_number = State()
   display_result = State()

@router.message(Command("category_search_random"))
async def category_search_random(message: Message, command: CommandObject, state: FSMContext):
    global recipes_for_display
    if command.args is None or command.args.isalpha():
        await message.answer("Неправильное указание числа. Добавьте число арабскими цифрами через пробел после '/category_search_random'")
    elif command.args is None or not command.args.isdigit():
        await message.answer("Неправильное указание числа. Добавьте число арабскими цифрами через пробел после '/category_search_random'")
    await state.set_data({'searched_number': int(command.args)})

    builder_ = ReplyKeyboardBuilder()
    async with aiohttp.ClientSession() as session:
        async with session.get(url='http://www.themealdb.com/api/json/v1/1/list.php?c=list') as resp:
            resp_ = await resp.json()
            
            for _ in resp_['meals']:
                builder_.add(types.KeyboardButton(text=_['strCategory']))
                recipes_for_display.append(_['strCategory'])
            builder_.adjust(5)
            
    await message.answer(
        f"Укажите категорию:",
        reply_markup=builder_.as_markup(resize_keyboard=True),
    )
    await state.set_state(searched_number.await_number.state)

@router.message(searched_number.await_number)
async def meals(message: types.Message, state: FSMContext):
    global recipes_for_display
    meals = await state.get_data()
    if message.text in recipes_for_display:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"http://www.themealdb.com/api/json/v1/1/filter.php?c={message.text}") as resp:
                data = await resp.json()
        meals_dict={}
        for _ in range(len(data['meals'])):
            meals_dict[data['meals'][_]['strMeal']] = data['meals'][_]["idMeal"]
        meals_dict_translated={}
        for key, value in meals_dict.items():
            translated_key = translator.translate(key, dest='ru').text
            meals_dict_translated[translated_key] = value
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Вывести найденные рецепты")],],
            resize_keyboard=True,
        )
        if meals['searched_number'] > len(meals_dict):
            await message.answer(f"К сожалению, количество обнаруженных блюд категории {message.text} меньше искомого, и составляет {len(meals_dict)}. \n"
                                 f"Вот все обнаруженные блюда: "
                                 f"{', '.join(meals_dict_translated.keys())}", reply_markup=keyboard)
            await state.set_data({'id_of_recepts': meals_dict_translated})
        else:
            list_of_keys = list(meals_dict_translated.keys())
            rand_keys = list(random.sample(list_of_keys, k=int(meals['searched_number'])))
            rand_meals_dict={key: meals_dict_translated[key] for key in rand_keys}
            await message.answer(f"Обнаружено {meals['searched_number']} случайное(ых) "
                                 f"блюд(а) в категории {message.text}: "
                                 f"{', '.join(rand_meals_dict.keys())}", reply_markup=keyboard)
            await state.set_data({'id_of_recepts' : rand_meals_dict})
        await state.set_state(searched_number.display_result.state)
    else:
        await message.answer('Ошибка в указании категории, повторите запрос')

@router.message(searched_number.display_result)
async def recipe_id(message: types.Message, state: FSMContext):
    if message.text == 'Вывести найденные рецепты':
        meals_state = await state.get_data()
        for meal, id in meals_state['id_of_recepts'].items():
            async with aiohttp.ClientSession() as session:
                async with session.get(url=f"http://www.themealdb.com/api/json/v1/1/lookup.php?i={int(id)}") as resp:
                    data = await resp.json()
            ing_dict = {}
            for _ in range(1, 21):
                if data['meals'][0][f'strIngredient{_}'] is None:
                    next
                elif data['meals'][0][f'strIngredient{_}'] == "":
                    next
                else:
                    ing_dict[data['meals'][0][f'strIngredient{_}']] = data['meals'][0][f'strMeasure{_}']
            str_ing_dict = '\n '.join([f'{key}: {value}' for key, value in ing_dict.items()])
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="/start")]],
                resize_keyboard=True,
            )
            display_message = (f"{meal}\n\n"
                       f"{translator.translate(data['meals'][0]['strInstructions'], dest='ru').text}"
                       f"\n\n Ингридиенты:\n {translator.translate(str_ing_dict, dest='ru').text}")
            if len(display_message) > 4096:
                display_messages = [display_message[i:i + 4096] for i in range(0, len(display_message), 4096)]
                for message_ in display_messages:
                    await message.answer(message_, reply_markup=keyboard)
            else:
                await message.answer(display_message, reply_markup=keyboard)
    else:
        await message.answer(f'Поле чата только для команд. Введите команду или воспользуйтесь кнопками снизу')

@router.message()
async def commands(message: types.Message):
    response = as_list(
        as_marked_section(
            Bold("Ошибка!"),
            "Команда не распознана, пожалуйста, введите /start для корректного начала работы бота или '/category_search_random (число)' для просмотра категорий блюд. "
            "\n Либо воспользуйтесь функциональными кнопками снизу с:"
        ),
    )
    await message.answer(
        **response.as_kwargs()
    )
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram import Dispatcher

from utils.database import DataBase

router = Router()


class AddWord(StatesGroup):
    entering_foreign = State()
    entering_lang = State()
    entering_native = State()
    entering_group = State()


@router.message(StateFilter(None), Command("add"))
async def start_word_add(message: Message, state: FSMContext):
    await message.answer(
        "Let's add a new word or phrase!\n"
        "Send to me the word or phrase in the foreign language.\n"
        "If you want to input multiple translations,\n"
        "just write words separating them using ', '(comma and space)"
    )
    await state.set_state(AddWord.entering_foreign)


@router.message(AddWord.entering_foreign)
async def process_foreign(message: Message, state: FSMContext):
    await state.update_data(foreign=message.text)
    await message.answer("Send to me a code of foreign language (e.g en, ru, aa)")
    await state.set_state(AddWord.entering_lang)


@router.message(AddWord.entering_lang)
async def process_lang(message: Message, state: FSMContext):
    await state.update_data(lang=message.text)
    await message.answer("Send to me the translation in your native language")
    await state.set_state(AddWord.entering_native)


@router.message(AddWord.entering_native)
async def process_native(message: Message, state: FSMContext):
    await state.update_data(native=message.text)
    await message.answer("Send to me the group name for this word, or leave empty for default group")
    await state.set_state(AddWord.entering_group)


@router.message(AddWord.entering_group)
async def process_group(message: Message, state: FSMContext, dispatcher: Dispatcher):
    user_data = await state.get_data()
    db = dispatcher["db"]
    db.input_word(message.chat.id,
                  user_data["foreign"],
                  user_data["lang"],
                  user_data["native"],
                  message.text)
    await message.answer("The word has been added successfully!")
    await state.set_state()

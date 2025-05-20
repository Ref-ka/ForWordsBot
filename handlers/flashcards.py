from aiogram import Router, F, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
)
import random

router = Router()


class Flashcards(StatesGroup):
    ask_random = State()
    ask_groups = State()
    ask_langs = State()
    in_flash = State()
    finished = State()


@router.message(Command("flash"))
async def start_flashcards(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Yes")], [KeyboardButton(text="No")]],
        resize_keyboard=True
    )
    await message.answer("Do you want the flashcards to be randomized?", reply_markup=kb)
    await state.set_state(Flashcards.ask_random)


@router.message(Flashcards.ask_random)
async def process_flashcard_random(message: Message, state: FSMContext):
    if message.text not in ("Yes", "No"):
        await message.answer("Your answer isn't correct. You need to just write 'Yes' or 'No'.")
        return
    await state.update_data(random=(message.text == "Yes"))
    await message.answer(
        "Select groups for flashcards (comma with space separated) or type 'all' for all groups:",
        reply_markup=None
    )
    await state.set_state(Flashcards.ask_groups)


@router.message(Flashcards.ask_groups)
async def process_flashcard_groups(message: Message, state: FSMContext):
    groups = [] if message.text.lower() == "all" else message.text.split(", ")
    await state.update_data(groups=groups)
    await message.answer(
        "Select languages (comma and space separated) or type 'all' for all languages:"
    )
    await state.set_state(Flashcards.ask_langs)


@router.message(Flashcards.ask_langs)
async def process_flashcard_languages(message: Message, state: FSMContext, dispatcher: Dispatcher):
    langs = [] if message.text.lower() == "all" else message.text.split(", ")
    data = await state.get_data()
    db = dispatcher["db"]
    words = db.get_flash_words(message.chat.id, data["groups"], langs)
    if not words:
        await message.answer("No words found for the selected filters.")
        await state.clear()
        return
    if data["random"]:
        random.shuffle(words)
    await state.update_data(words=words, index=0)
    await show_flashcard(message, state)


async def show_flashcard(message: Message, state: FSMContext):
    data = await state.get_data()
    index = data["index"]
    words = data["words"]
    if index >= len(words):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Retry These Words", callback_data="flash_retry")],
            [InlineKeyboardButton(text="📂 Choose New Groups/Languages", callback_data="flash_new")]
        ])
        await message.answer("You've gone through all words! What do you want to do next?", reply_markup=kb)
        await state.set_state(Flashcards.finished)
        return
    word = words[index]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Show Answer", callback_data="flash_show")]
    ])
    await message.answer(f"Flashcard:\nWord: {word[0]}\nWhat is the translation?", reply_markup=kb)
    await state.set_state(Flashcards.in_flash)


@router.callback_query(Flashcards.in_flash, F.data == "flash_show")
async def flash_show_answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data["index"]
    word = data["words"][index]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Next", callback_data="flash_next")]
    ])
    await call.message.edit_text(f"Flashcard:\nWord: {word[0]}\nTranslation: {word[1]}", reply_markup=kb)


@router.callback_query(Flashcards.in_flash, F.data == "flash_next")
async def flash_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(index=data["index"] + 1)
    await show_flashcard(call.message, state)


@router.callback_query(Flashcards.finished, F.data == "flash_retry")
async def flash_retry(call: CallbackQuery, state: FSMContext):
    await state.update_data(index=0)
    await show_flashcard(call.message, state)


@router.callback_query(Flashcards.finished, F.data == "flash_new")
async def flash_new(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Let's choose new words! Enter the groups you want to study:")
    await state.set_state(Flashcards.ask_groups)

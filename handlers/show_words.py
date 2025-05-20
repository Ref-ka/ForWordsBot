from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

router = Router()


class ShowWords(StatesGroup):
    entering_group = State()
    entering_languages = State()


@router.message(StateFilter(None), Command("show"))
async def show_words(message: Message, state: FSMContext):
    await message.answer(
        "What group do you want to see?\n"
        "If you want to see multiple groups\njust write them separating by ', '(comma and space)\n"
        "If you want to see all groups write 'all'"
    )
    await state.set_state(ShowWords.entering_group)


@router.message(ShowWords.entering_group)
async def process_groups(message: Message, state: FSMContext):
    groups = message.text.split(", ")
    if groups == ["all"]:
        await state.update_data(groups=[])
    else:
        await state.update_data(groups=groups)
    await message.answer(
        "What languages do you want to see?\n"
        "If you want to see multiple langs\njust write them separating by ', '(comma and space)\n"
        "If you want to see all lang write 'all'"
    )
    await state.set_state(ShowWords.entering_languages)


@router.message(ShowWords.entering_languages)
async def process_languages(message: Message, state: FSMContext, dispatcher: Dispatcher):
    langs = message.text.split(", ")
    if langs == ["all"]:
        langs = []
    groups = await state.get_data()
    groups = groups["groups"]
    db = dispatcher["db"]
    words = db.get_show_words(
        message.chat.id,
        groups,
        langs
    )
    msg_text = "Your words:\n\n"
    for line in words:
        msg_text += f"{line[1]}  --  {line[0]} \n    Group: {line[2]}, Lang: {line[3]}\n\n"
    await message.answer(
        msg_text
    )
    await state.set_state()

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
import random

router = Router()


class Flash(StatesGroup):
    ACTIVE = State()
    DONE = State()


@router.message(Command("flash"))
async def cmd_flash(message: Message, state: FSMContext):
    await state.clear()  # reset any old data
    kb = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[[
            InlineKeyboardButton(text="Yes", callback_data="rnd:yes"),
            InlineKeyboardButton(text="No", callback_data="rnd:no")]]
    )
    await message.answer("Randomize cards?", reply_markup=kb)
    await state.set_state(Flash.ACTIVE)
    await state.update_data(step="ask_random")


# handle the YES/NO inline buttons
@router.callback_query(Flash.ACTIVE, F.data.startswith("rnd:"))
async def cq_random(call: CallbackQuery, state: FSMContext):
    is_rand = call.data.split(":", 1)[1] == "yes"
    await state.update_data(random=is_rand, step="ask_groups")
    await call.message.edit_text("Enter groups (comma-separated) or ‘all’:", reply_markup=None)


# now single message handler for the rest of the text inputs
@router.message(Flash.ACTIVE)
async def flash_flow(message: Message, state: FSMContext, dispatcher):
    data = await state.get_data()
    step = data.get("step")

    # 1) groups
    if step == "ask_groups":
        groups = [] if message.text.lower() == "all" else message.text.split(",")
        await state.update_data(groups=groups, step="ask_langs")
        return await message.answer("Enter languages (comma-separated) or ‘all’:")

        # 2) langs
    if step == "ask_langs":
        langs = [] if message.text.lower() == "all" else message.text.split(",")
        await state.update_data(langs=langs)

        # fetch words
        db = dispatcher["db"]
        words = db.get_flash_words(message.chat.id, data["groups"], langs)
        if not words:
            await state.clear()
            return await message.answer("No words found with those filters.")

        if data["random"]:
            random.shuffle(words)

        # store and show first card
        await state.update_data(words=words, idx=0, step="show")
        return await _show_card(message, state)


# helper to display a card
async def _show_card(target, state: FSMContext):
    data = await state.get_data()
    w = data["words"][data["idx"]]
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Show Answer", callback_data="action:show")
    ]]
    )
    await target.answer(f"🔤  {w[0]}\nWhat’s the translation?", reply_markup=kb)


# show answer
@router.callback_query(Flash.ACTIVE, F.data == "action:show")
async def cq_show(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    w = data["words"][data["idx"]]
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Next", callback_data="action:next")]]
    )
    await call.message.edit_text(f"🔤  {w[0]}\n✅  {w[1]}", reply_markup=kb)


# next card or finish
@router.callback_query(Flash.ACTIVE, F.data == "action:next")
async def cq_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data["idx"] + 1

    # if more cards left
    if idx < len(data["words"]):
        await state.update_data(idx=idx)
        return await _show_card(call.message, state)

    # else finished
    kb = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Retry", callback_data="action:retry"),
            InlineKeyboardButton(text="📂 New", callback_data="action:new"),
        ]]
    )
    await call.message.answer("You’ve seen them all. What now?", reply_markup=kb)
    await state.set_state(Flash.DONE)


# retry same deck
@router.callback_query(Flash.DONE, F.data == "action:retry")
async def cq_retry(call: CallbackQuery, state: FSMContext):
    await state.update_data(idx=0)
    await state.set_state(Flash.ACTIVE)
    return await _show_card(call.message, state)


# pick new filters
@router.callback_query(Flash.DONE, F.data == "action:new")
async def cq_new(call: CallbackQuery, state: FSMContext):
    await state.update_data(step="ask_groups")
    await state.set_state(Flash.ACTIVE)
    return await call.message.answer("Enter groups (comma-separated) or ‘all’:")

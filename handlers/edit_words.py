from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


class EditWord(StatesGroup):
    waiting_for_pair = State()
    choosing_action = State()
    waiting_confirmation = State()
    waiting_new_value = State()


FIELD_MAP = {
    'fgn': ("Enter new foreign word:", "change_foreign_word", "✅ Foreign word changed."),
    'ntv': ("Enter new native word:", "change_native_word", "✅ Native word changed."),
    'grp': ("Enter new group:", "change_group", "✅ Group changed."),
    'lng': ("Enter new lang code:", "change_lang_code", "✅ Lang code changed."),
}


@router.message(Command("edit"))
async def cmd_edit(message: Message, state: FSMContext):
    await message.answer("Send me `(native_word) (lang_code)`")
    await state.set_state(EditWord.waiting_for_pair)


@router.message(EditWord.waiting_for_pair)
async def select_word(message: Message, state: FSMContext, dispatcher):
    parts = message.text.split()
    if len(parts) != 2:
        return await message.answer("⚠️ Please send exactly two words: `(native) (lang_code)`")
    native, lang = parts
    db = dispatcher["db"]
    res = db.get_word_for_editing(message.chat.id, native, lang)
    if not res:
        return await message.answer("❌ No such word. Try again.")
    word = res[0]
    await state.update_data(word=word)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Delete", callback_data="del"),
                InlineKeyboardButton(text="✏️ Change", callback_data="change")
            ]
        ]
    )
    await message.answer(f"Editing:\n{word}", reply_markup=kb)
    await state.set_state(EditWord.choosing_action)


@router.callback_query(EditWord.choosing_action, F.data == "del")
async def confirm_delete(cb: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Yes, delete 🗑", callback_data="del_yes"),
        InlineKeyboardButton(text="No, cancel ❌", callback_data="del_no"),
    ]])
    data = await state.get_data()
    await cb.message.edit_text(f"Confirm deletion of:\n{data['word']}", reply_markup=kb)
    await state.set_state(EditWord.waiting_confirmation)


@router.callback_query(EditWord.waiting_confirmation, F.data == "del_yes")
async def do_delete(cb: CallbackQuery, state: FSMContext, dispatcher):
    data = await state.get_data()
    word = data["word"]
    dispatcher["db"].delete_word(cb.message.chat.id, word[1], word[3])
    await cb.message.edit_text("✅ Word deleted.")
    await state.clear()


@router.callback_query(EditWord.waiting_confirmation, F.data == "del_no")
async def cancel_delete(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("❌ Deletion canceled.")
    await state.clear()


# ---- NEW: handle “change” clicks in the correct state ----
@router.callback_query(EditWord.choosing_action, F.data == "change")
async def ask_field(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    word = data["word"]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Foreign", callback_data="change_fgn"),
                InlineKeyboardButton(text="Native", callback_data="change_ntv"),
            ],
            [
                InlineKeyboardButton(text="Group", callback_data="change_grp"),
                InlineKeyboardButton(text="Lang", callback_data="change_lng"),
            ],
        ]
    )
    await cb.message.edit_text(f"Which field to change?\n{word}", reply_markup=kb)


@router.callback_query(EditWord.choosing_action, F.data.startswith("change_"))
async def ask_new_value(cb: CallbackQuery, state: FSMContext):
    tag = cb.data.split("_", 1)[1]  # e.g. "fgn"
    prompt, _, _ = FIELD_MAP[tag]
    await state.update_data(field_tag=tag)
    await cb.message.edit_text(prompt)
    await state.set_state(EditWord.waiting_new_value)


@router.message(EditWord.waiting_new_value)
async def do_change(message: Message, state: FSMContext, dispatcher):
    data = await state.get_data()
    word = data["word"]
    tag = data["field_tag"]
    prompt, method_name, success = FIELD_MAP[tag]
    db = dispatcher["db"]
    getattr(db, method_name)(
        message.chat.id,
        word[1],  # old native
        message.text,  # new value
        word[3],  # old lang
    )
    await message.answer(success)
    await state.clear()

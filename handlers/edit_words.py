from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


class EditWord(StatesGroup):
    waiting_for_pair = State()  # after /edit
    choosing_action = State()  # after showing delete/change buttons
    waiting_confirmation = State()  # confirm delete
    waiting_new_value = State()  # entering new value for a field


# map short field tags to (prompt, db_method_name, success_text)
FIELD_MAP = {
    'fgn': ("Enter new foreign word:", "change_foreign_word", "✅ Foreign word changed."),
    'ntv': ("Enter new native word:", "change_native_word", "✅ Native word changed."),
    'grp': ("Enter new group:", "change_group", "✅ Group changed."),
    'lng': ("Enter new lang code:", "change_lang_code", "✅ Lang code changed."),
}


@router.message(Command("edit"))
async def cmd_edit(message: Message, state: FSMContext):
    await message.answer("Send me: <native_word> <lang_code>")
    await state.set_state(EditWord.waiting_for_pair)


@router.message(EditWord.waiting_for_pair)
async def select_word(message: Message, state: FSMContext, dispatcher):
    parts = message.text.split()
    if len(parts) != 2:
        return await message.answer("⚠️ Please send exactly two words: `<native> <lang_code>`.")
    native, lang = parts
    db = dispatcher["db"]
    res = db.get_word_for_editing(message.chat.id, native, lang)
    if not res:
        return await message.answer("❌ No such word. Try again:")
    word = res[0]
    await state.update_data(word=word)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Delete", callback_data="del"),
             InlineKeyboardButton(text="✏️ Change", callback_data="change")],
        ]
    )
    await message.answer(f"Editing:\n{word}", reply_markup=kb)
    await state.set_state(EditWord.choosing_action)


@router.callback_query(EditWord.choosing_action, F.data.in_(["del", "change"]))
async def choose_action(cb: CallbackQuery, state: FSMContext, dispatcher):
    data = await state.get_data()
    word = data["word"]
    if cb.data == "del":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="Yes, delete 🗑", callback_data="del_yes"),
                InlineKeyboardButton(text="No, cancel ❌", callback_data="del_no"),
            ]]
        )
        await cb.message.edit_text(f"Confirm deletion of:\n{word}", reply_markup=kb)
        await state.set_state(EditWord.waiting_confirmation)

    else:  # change
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
        await cb.message.edit_text(f"Choose field to change:\n{word}", reply_markup=kb)
        # state remains choosing_action


# confirm delete or field‐selection
@router.callback_query(EditWord.waiting_confirmation, F.data.in_(["del_yes", "del_no"]) | F.data.startswith("change_"))
async def on_confirm_or_field(cb: CallbackQuery, state: FSMContext, dispatcher):
    db = dispatcher["db"]
    data = await state.get_data()
    word = data["word"]

    if cb.data == "del_yes":
        db.delete_word(cb.message.chat.id, word[1], word[3])
        await cb.message.edit_text("✅ Word deleted.")
        return await state.clear()

    if cb.data == "del_no":
        await cb.message.edit_text("❌ Deletion canceled.")
        return await state.clear()

    # else it's change_<tag>
    tag = cb.data.split("_", 1)[1]  # e.g. "fgn"
    prompt, method_name, _ = FIELD_MAP[tag]
    await state.update_data(field_tag=tag)
    await cb.message.edit_text(prompt)
    await state.set_state(EditWord.waiting_new_value)


@router.message(EditWord.waiting_new_value)
async def set_new_value(message: Message, state: FSMContext, dispatcher):
    data = await state.get_data()
    word = data["word"]
    tag = data["field_tag"]
    prompt, method_name, success = FIELD_MAP[tag]

    # dynamically call e.g. db.change_foreign_word(chat_id, old_native, new_value, old_lang)
    db = dispatcher["db"]
    getattr(db, method_name)(
        message.chat.id,
        word[1],  # old native
        message.text,  # new value
        word[3],  # old lang
    )
    await message.answer(success)
    await state.clear()

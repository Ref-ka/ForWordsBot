from aiogram import Router, F, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
)

router = Router()


# --- Edit Word FSM ---

class EditWord(StatesGroup):
    waiting_native_lang = State()
    choosing_action = State()
    changing_foreign = State()
    changing_native = State()
    changing_group = State()
    changing_lang = State()
    confirming_delete = State()


@router.message(Command("edit"))
async def edit_words(message: Message, state: FSMContext):
    await message.answer("Write word in native language and foreign lang code (separated by space)")
    await state.set_state(EditWord.waiting_native_lang)


@router.message(EditWord.waiting_native_lang)
async def select_edit_word(message: Message, state: FSMContext, dispatcher: Dispatcher):
    try:
        native, lang = message.text.split(" ")
    except Exception:
        await message.answer("You need to write two words: word in native and lang code\nFor example: (target ru)")
        return
    db = dispatcher["db"]
    data = db.get_word_for_editing(message.chat.id, native, lang)
    if not data:
        await message.answer("There are no any words with this pair of native word and lang!\nEnter again:")
        return
    word = data[0]
    await state.update_data(word=word)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Delete", callback_data="edit_del"),
         InlineKeyboardButton(text="Change", callback_data="edit_change")]
    ])
    await message.answer(f"Editing word:\n{word}", reply_markup=kb)
    await state.set_state(EditWord.choosing_action)


@router.callback_query(EditWord.choosing_action, F.data == "edit_del")
async def confirm_delete(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Yes", callback_data="edit_del_yes"),
         InlineKeyboardButton(text="No", callback_data="edit_del_no")]
    ])
    data = await state.get_data()
    await call.message.edit_text(f"Deleting word:\n{data['word']}\nConfirm?", reply_markup=kb)
    await state.set_state(EditWord.confirming_delete)


@router.callback_query(EditWord.confirming_delete, F.data == "edit_del_yes")
async def do_delete(call: CallbackQuery, state: FSMContext, dispatcher: Dispatcher):
    data = await state.get_data()
    word = data['word']
    db = dispatcher["db"]
    db.delete_word(call.message.chat.id, word[1], word[3])
    await call.message.answer("Word deleted successfully.")
    await state.clear()


@router.callback_query(EditWord.confirming_delete, F.data == "edit_del_no")
async def cancel_delete(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Deletion cancelled.")
    await state.clear()


@router.callback_query(EditWord.choosing_action, F.data == "edit_change")
async def choose_change(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Change foreign", callback_data="edit_change_fgn"),
         InlineKeyboardButton(text="Change native", callback_data="edit_change_ntv")],
        [InlineKeyboardButton(text="Change group", callback_data="edit_change_grp"),
         InlineKeyboardButton(text="Change lang code", callback_data="edit_change_lng")]
    ])
    data = await state.get_data()
    await call.message.edit_text(f"Choose what to change:\n{data['word']}", reply_markup=kb)


@router.callback_query(EditWord.choosing_action, F.data == "edit_change_fgn")
async def ask_foreign(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Enter new foreign word:")
    await state.set_state(EditWord.changing_foreign)


@router.message(EditWord.changing_foreign)
async def do_change_foreign(message: Message, state: FSMContext, dispatcher: Dispatcher):
    data = await state.get_data()
    word = data['word']
    db = dispatcher["db"]
    db.change_foreign_word(message.chat.id, word[1], message.text, word[3])
    await message.answer("Foreign word has been changed!")
    await state.clear()


@router.callback_query(EditWord.choosing_action, F.data == "edit_change_ntv")
async def ask_native(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Enter new native word:")
    await state.set_state(EditWord.changing_native)


@router.message(EditWord.changing_native)
async def do_change_native(message: Message, state: FSMContext, dispatcher: Dispatcher):
    data = await state.get_data()
    word = data['word']
    db = dispatcher["db"]
    db.change_native_word(message.chat.id, word[1], message.text, word[3])
    await message.answer("Native word has been changed!")
    await state.clear()


@router.callback_query(EditWord.choosing_action, F.data == "edit_change_grp")
async def ask_group(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Enter new group:")
    await state.set_state(EditWord.changing_group)


@router.message(EditWord.changing_group)
async def do_change_group(message: Message, state: FSMContext, dispatcher: Dispatcher):
    data = await state.get_data()
    word = data['word']
    db = dispatcher["db"]
    db.change_group(message.chat.id, word[1], message.text, word[3])
    await message.answer("Group of word has been changed!")
    await state.clear()


@router.callback_query(EditWord.choosing_action, F.data == "edit_change_lng")
async def ask_lang(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Enter new lang code:")
    await state.set_state(EditWord.changing_lang)


@router.message(EditWord.changing_lang)
async def do_change_lang(message: Message, state: FSMContext, dispatcher: Dispatcher):
    data = await state.get_data()
    word = data['word']
    db = dispatcher["db"]
    db.change_lang_code(message.chat.id, word[1], message.text, word[3])
    await message.answer("Lang code of word has been changed!")
    await state.clear()

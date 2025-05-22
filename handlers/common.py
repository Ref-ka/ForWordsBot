from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(Command(commands=["cancel"]))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="❌ Action canceled! If you need anything else, just let me know 😊"
    )


@router.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    text = (
        "✨ <b>Here’s what I can do for you:</b>\n\n"
        "➕ <b>Add words</b>: /add\n"
        "✏️ <b>Edit words</b>: /edit\n"
        "📋 <b>Show words</b>: /show\n"
        "🃏 <b>Flashcards</b>: /flash\n"
        "⏰ <b>Set reminder</b>: /set_reminder\n"
        "📤 <b>Export words</b>: /export\n"
        "📝 <b>Survey</b>: /survey"
    )
    await message.answer(
        "👋 <b>Welcome to ForWordsBot!</b>\n\n"
        "I'm here to help you learn and manage your vocabulary. Choose an option below to get started:\n\n"
        f"{text}",
        parse_mode="HTML"
    )


@router.message(Command(commands=["survey"]))
async def send_survey(message: Message):
    await message.answer(
        "📝 <b>We value your feedback!</b>\n\n"
        "Would you like to help us improve? Please take a quick survey about this bot:\n"
        "🔗 <a href='https://forms.gle/WTaK4Qed9GRKr8BcA'>Take the survey</a>",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

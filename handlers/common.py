from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(Command(commands=["cancel"]))
@router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Action have been canceled!"
    )


@router.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    text = """
    Add words: /add\n
    Edit words: /edit\n
    Show words: /show\n
    Flashcards: /flash\n
    Set reminder: /set_reminder\n
    Export words: /export\n
    Survey: /survey
    """
    await message.answer(
        "Welcome to the ForWordsBot! Choose an option:\n" + text
    )


@router.message(Command(commands=["survey"]))
async def send_survey(message: Message):
    await message.answer(
        "You can take a survey about this telegram bot:\nhttps://forms.gle/WTaK4Qed9GRKr8BcA"
    )

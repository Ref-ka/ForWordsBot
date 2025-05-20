from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Dispatcher

router = Router()


@router.message(Command("add"))
async def add_word(
    message: Message,
    dispatcher: Dispatcher,
):
    """
    Usage:
      /add foreign|lang|native [|group]
    Examples:
      /add hello|en|привет
      /add dog|en|собака|animals
    """
    # split the command from its arguments
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer(
            "❗️ Please use:\n"
            "/add foreign|lang|native [|group]\n"
            "e.g. /add cat|en|кошка|pets"
        )

    # parse and trim
    fields = [f.strip() for f in parts[1].split("|")]
    if not (3 <= len(fields) <= 4):
        return await message.answer(
            "❗️ Wrong format. You need 3 or 4 items separated by '|'.\n"
            "e.g. /add hello|en|привет|greetings"
        )

    foreign, lang, native = fields[0], fields[1], fields[2]
    group = fields[3] if len(fields) == 4 else ""  # optional

    # save to DB
    db = dispatcher["db"]
    db.input_word(
        chat_id=message.chat.id,
        foreign=foreign,
        lang=lang,
        native=native,
        group=group
    )

    await message.answer("✅ Your word has been added!")
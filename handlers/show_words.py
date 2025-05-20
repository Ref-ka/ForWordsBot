from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("show"))
async def show_words(
        message: Message,
        dispatcher: Dispatcher,  # Aiogram will inject your Dispatcher here
):
    """
    Usage:
      /show <groups> | <languages>
    Examples:
      /show all | all
      /show animals, food | en, de
      /show animals | all
    """
    # remove the "/show" and strip whitespace
    payload = message.text[len("/show"):].strip()
    if not payload:
        return await message.answer(
            "❗️Usage: /show (groups) | (languages)\n"
            "Example: /show animals, food | en, de\n"
            "Use 'all' to not filter."
        )

    # Split into "groups" and "langs" by the pipe character
    try:
        groups_part, langs_part = [p.strip() for p in payload.split("|", maxsplit=1)]
    except ValueError:
        return await message.answer(
            "❗️Invalid format. Please use:\n"
            "  /show (groups) | (languages)\n"
            "E.g. /show animals, food | en, de"
        )

    # Parse groups
    if groups_part.lower() == "all":
        groups = []
    else:
        groups = [g.strip() for g in groups_part.split(",") if g.strip()]

    # Parse languages
    if langs_part.lower() == "all":
        langs = []
    else:
        langs = [l.strip() for l in langs_part.split(",") if l.strip()]

    # Fetch from your DB (you said you store it under dispatcher["db"])
    db = dispatcher["db"]
    # assuming get_show_words returns a list of tuples
    # [(translation, original, group, lang), ...]
    words = db.get_show_words(
        chat_id=message.chat.id,
        groups=groups,
        langs=langs,
    )

    if not words:
        return await message.answer("ℹ️ No words found with those filters.")

    # Build a single reply
    lines = []
    for translation, original, grp, lang in words:
        lines.append(f"{original}  —  {translation}\n   ▪ group: {grp}, lang: {lang}")

    text = "📝 Your words:\n\n" + "\n\n".join(lines)
    await message.answer(text)

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from utils.examples import get_examples

router = Router()

USAGE = (
    "Examples command\n\n"
    "How to use:\n"
    "/examples word|lang_code[|limit][|llm]\n\n"
    "- word — the word or phrase to get examples for\n"
    "- lang_code — 3-letter language code (e.g., eng, rus, deu)\n"
    "- limit — optional number of examples (1–10). If you skip it, a default is used. To enable LLM without setting a limit, leave it empty: ||llm\n"
    "- llm — optional. Add llm to include AI-generated examples (more creative, may be inaccurate)\n\n"
    "Examples:\n\n"
    "- /examples dog|eng\n"
    "- /examples laufen|deu|7\n"
    "- /examples забор|rus||llm\n"
)


@router.message(Command("examples"))
async def cmd_examples(message: Message, command: CommandObject):
    if not command.args:
        return await message.answer(USAGE)

    fields = [f.strip() for f in command.args.split("|")]
    if not (2 <= len(fields) <= 4):
        return await message.answer(USAGE)

    word = fields[0]
    lang = fields[1].lower()
    print(f"word: {word}, lang: {lang}")

    try:
        limit = int(fields[2]) if len(fields) == 3 else 5
    except ValueError:
        limit = 5

    try:
        llm = True if len(fields) == 4 and fields[3] == "llm" else False
    except ValueError:
        llm = False

    if limit <= 0:
        limit = 5
    limit = min(limit, 10)

    examples = await get_examples(word=word, language_code=lang, limit=limit, llm=llm)
    if not examples:
        return await message.answer(
            "Sorry, our database and AI model doesn't know much about this word or language. "
            "Try a different word or language!"
        )

    text = "Here are your examples!\n" + "\n".join(f"• {ex}" for ex in examples)
    await message.answer(text)

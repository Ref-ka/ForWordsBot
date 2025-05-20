import io
import csv
import json
from aiogram import Router, F, Dispatcher
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
)

router = Router()


@router.message(Command("export"))
async def cmd_export(message: Message):
    # build an inline keyboard with three buttons
    buttons = [[
        InlineKeyboardButton(text=f, callback_data=f"export:{f}")
        for f in ("txt", "csv", "json")
    ]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons, row_width=3)
    await message.answer("Choose export format:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("export:"))
async def cb_export_format(query: CallbackQuery, dispatcher: Dispatcher):
    # parse format out of the callback data
    fmt = query.data.split(":", maxsplit=1)[1]
    # fetch your data however you like
    db = dispatcher["db"]
    words = db.get_show_words(query.message.chat.id)
    words = [(row[0], row[1]) for row in words]

    if fmt == "txt":
        payload = "\n".join(f"{f} --- {n}" for f, n in words)
        bio = io.BytesIO(payload.encode("utf-8"))
        filename = "words.txt"

    elif fmt == "csv":
        # write CSV into a StringIO and then get bytes
        s = io.StringIO()
        w = csv.writer(s)
        w.writerow(["Foreign", "Native"])
        w.writerows(words)
        bio = io.BytesIO(s.getvalue().encode("utf-8"))
        filename = "words.csv"

    elif fmt == "json":
        payload = json.dumps(
            [{"foreign": f, "native": n} for f, n in words],
            ensure_ascii=False,
            indent=2,
        )
        bio = io.BytesIO(payload.encode("utf-8"))
        filename = "words.json"

    else:
        # invalid format
        await query.answer("Invalid format, try again.", show_alert=True)
        return

    # wrap our BytesIO in an InputFile and send
    bio.seek(0)
    document = BufferedInputFile(bio.read(), filename)  # , filename=filename
    await query.message.answer_document(document)

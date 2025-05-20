import csv
import json
import shutil
import tempfile
import aiofiles
import os
from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, FSInputFile

from keyboards.row import make_row_keyboard

router = Router()


class ExportWords(StatesGroup):
    entering_export_format = State()


async def make_txt(words, message: Message):
    with tempfile.NamedTemporaryFile('w+', encoding='utf-8', delete=False, suffix='.txt') as tmp:
        filename = tmp.name

    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        for line in words:
            await file.write(f"{line[0]} --- {line[1]}\n")

    await message.reply_document(FSInputFile(filename))
    os.remove(filename)


async def make_csv(words, message: Message):
    with tempfile.NamedTemporaryFile('w+', encoding='utf-8', delete=False, suffix='.csv', newline='') as tmp:
        filename = tmp.name

    with open(filename, "w", encoding="utf-8", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Foreign", "Native"])
        for line in words:
            writer.writerow([line[0], line[1]])

    await message.reply_document(FSInputFile(filename))
    os.remove(filename)


async def make_json(words, message: Message):
    with tempfile.NamedTemporaryFile('w+', encoding='utf-8', delete=False, suffix='.json') as tmp:
        filename = tmp.name

    words_list = [{"foreign": line[0], "native": line[1]} for line in words]
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(json.dumps(words_list, ensure_ascii=False, indent=2))

    await message.reply_document(FSInputFile(filename))
    os.remove(filename)


@router.message(StateFilter(None), Command("export"))
async def export_words(message: Message, state: FSMContext):
    await message.answer("Choose export format: txt, csv, or json",
                         reply_markup=make_row_keyboard(["txt", "csv", "json"], inline=False))
    await state.set_state(ExportWords.entering_export_format)


@router.message(ExportWords.entering_export_format)
async def process_export_format(message: Message, state: FSMContext, dispatcher: Dispatcher):
    export_format = message.text
    db = dispatcher["db"]
    words = db.get_show_words(message.chat.id)

    if export_format == "txt":
        await make_txt(words, message)
    elif export_format == "csv":
        await make_csv(words, message)
    elif export_format == "json":
        await make_json(words, message)
    else:
        await message.reply("Export option is invalid! Please enter again.",
                            reply_markup=make_row_keyboard(["txt", "csv", "json"], inline=False))
        await state.set_state(ExportWords.entering_export_format)
    await state.set_state()

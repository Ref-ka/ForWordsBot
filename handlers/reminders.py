from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
import asyncio
import random

router = Router()


# --- Reminder FSM ---

class Reminder(StatesGroup):
    group = State()
    interval = State()


reminder_timers = {}


@router.message(Command("set_reminder"))
async def make_reminder(message: Message, state: FSMContext):
    await message.answer("Enter the group for which to set a reminder (or type 'all'):")
    await state.set_state(Reminder.group)


@router.message(Reminder.group)
async def process_reminder_group(message: Message, state: FSMContext):
    await state.update_data(group=message.text.strip())
    await message.answer("Enter the time interval for the reminder (e.g., '10m', '2h', '1d'):")
    await state.set_state(Reminder.interval)


@router.message(Reminder.interval)
async def process_reminder_time(message: Message, state: FSMContext):
    time_input = message.text.strip().lower()
    chat_id = message.chat.id
    time_mapping = {"m": 60, "h": 3600, "d": 86400}
    try:
        unit = time_input[-1]
        value = int(time_input[:-1])
        if unit not in time_mapping:
            raise ValueError("Invalid time unit")
        interval = value * time_mapping[unit]
        if interval < 60 or interval > 2592000:
            raise ValueError("Time out of range")
    except Exception:
        await message.answer("Invalid time format. Please try again (e.g., '10m', '2h', '1d'):")
        return
    group = (await state.get_data())["group"]
    if chat_id not in reminder_timers:
        reminder_timers[chat_id] = []
    reminder_timers[chat_id].append({
        "group": group,
        "interval": interval,
        "time_input": time_input,
        "active": True
    })
    await message.answer(f"Reminder set for group '{group}' every {time_input}. Use /reminders to manage reminders.")
    await state.clear()
    await asyncio.create_task(reminder_task(chat_id, len(reminder_timers[chat_id]) - 1, message))


async def reminder_task(chat_id, idx, message):
    while True:
        reminder = reminder_timers[chat_id][idx]
        if reminder["active"]:
            await message.answer(f"Reminder: Review your words in group '{reminder['group']}'!")
        await asyncio.sleep(reminder["interval"])


@router.message(Command("reminders"))
async def list_reminders(message: Message):
    chat_id = message.chat.id
    if chat_id not in reminder_timers or not reminder_timers[chat_id]:
        await message.answer("You have no active reminders.")
        return
    response = "Your active reminders:\n"
    for i, reminder in enumerate(reminder_timers[chat_id], start=1):
        status = "Active" if reminder["active"] else "Inactive"
        response += f"{i}. Group: {reminder['group']}, Interval: {reminder['time_input']}, Status: {status}\n"
    response += "\nTo stop a reminder, use /stop_reminder (number)."
    response += "\nTo run a reminder, use /run_reminder (number)."
    response += "\nTo delete a reminder, use /delete_reminder (number)."
    print(response)
    await message.answer(response)


@router.message(Command("stop_reminder"))
async def stop_reminder(message: Message):
    chat_id = message.chat.id
    if chat_id not in reminder_timers or not reminder_timers[chat_id]:
        await message.answer("You have no active reminders to stop.")
        return
    try:
        index = int(message.text.split()[1]) - 1
        reminder_timers[chat_id][index]["active"] = False
        await message.answer(f"Reminder {index + 1} has been stopped.")
    except Exception:
        await message.answer("Invalid command. Use /stop_reminder <number> to stop a reminder.")


@router.message(Command("run_reminder"))
async def run_reminder(message: Message):
    chat_id = message.chat.id
    if chat_id not in reminder_timers or not reminder_timers[chat_id]:
        await message.answer("You have no inactive reminders to run.")
        return
    try:
        index = int(message.text.split()[1]) - 1
        reminder_timers[chat_id][index]["active"] = True
        await message.answer(f"Reminder {index + 1} has been launched.")
    except Exception:
        await message.answer("Invalid command. Use /run_reminder <number> to run a reminder.")


@router.message(Command("delete_reminder"))
async def delete_reminder(message: Message):
    chat_id = message.chat.id
    if chat_id not in reminder_timers or not reminder_timers[chat_id]:
        await message.answer("You have no reminders to delete.")
        return
    try:
        index = int(message.text.split()[1]) - 1
        reminder_timers[chat_id].pop(index)
        await message.answer(f"Reminder {index + 1} has been deleted.")
    except Exception:
        await message.answer("Invalid command. Use /delete_reminder <number> to delete a reminder.")

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

import config
import threading
import random
import csv
import json
from database import DataBase
from os import remove

TOKEN = config.TOKEN
bot = telebot.TeleBot(TOKEN)
db = DataBase()

# Caches for storing temporary data during conversations
load_cache = {}      # For /add word flow
show_cache = {}      # For showing list of words
edit_cache = {}      # For editing a selected word
flash_cache = {}     # For flashcards session
reminder_cache = {}  # For reminder settings
user_sessions = {}

# Dictionary to keep track of reminder timers per chat
reminder_timers = {}


# -------------------------------
# Menu and /start command
# -------------------------------
@bot.message_handler(commands=["start", "menu"])
def send_instruction(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Add Word", callback_data="menu_add"),
        InlineKeyboardButton("Edit Word", callback_data="menu_edit"),
        InlineKeyboardButton("Show Words", callback_data="menu_show"),
        InlineKeyboardButton("Flashcards", callback_data="menu_flash"),
        InlineKeyboardButton("Sort Words", callback_data="menu_sort"),
        InlineKeyboardButton("Set Reminder", callback_data="menu_reminder"),
        InlineKeyboardButton("Export Words", callback_data="menu_export")
    )
    bot.send_message(message.chat.id, "Welcome to the Foreign Words Bot! Choose an option:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def menu_handler(call):
    if call.data == "menu_add":
        start_input(call.message)
    elif call.data == "menu_edit":
        bot.send_message(call.message.chat.id, "Use /edit to edit words.")
    elif call.data == "menu_show":
        show_words(call.message)
    elif call.data == "menu_flash":
        start_flashcards(call.message)
    elif call.data == "menu_sort":
        bot.send_message(call.message.chat.id, "Sort words by which language? Type 'en' for foreign or 'ru' for native:")
        bot.register_next_step_handler(call.message, sort_words)
    elif call.data == "menu_reminder":
        bot.send_message(call.message.chat.id, "Enter the group for which to set a reminder (or type 'all'):")
        bot.register_next_step_handler(call.message, process_reminder_group)
    elif call.data == "menu_export":
        bot.send_message(call.message.chat.id, "Choose export format: txt, csv, or json:")
        bot.register_next_step_handler(call.message, upload_words_format)


def cancel_fsm(func):
    def wrapper(message):
        if message.text == "cancel":
            bot.send_message(message.chat.id, "Action has been canceled!")
            return
        else:
            func(message)
    return wrapper

# -------------------------------
# Adding new words (/add)
# -------------------------------
@bot.message_handler(commands=['add'])
def start_input(message):
    msg = bot.reply_to(message, "Let's make a card!\n"
                                "Send to me the word in the foreign language.\n"
                                "If you want to input multiple translations,\n"
                                "just write words separating them using ', '(comma and space)")
    bot.register_next_step_handler(msg, process_foreign_word)


@cancel_fsm
def process_foreign_word(message):
    load_cache[message.chat.id] = [message.text.lower()]
    msg = bot.reply_to(message, "Send to me a code of foreign language (e.g en, ru, aa)")
    bot.register_next_step_handler(msg, process_language_name)


@cancel_fsm
def process_language_name(message):
    load_cache[message.chat.id].append(message.text)
    msg = bot.reply_to(message, "Send to me the translation in your native language")
    bot.register_next_step_handler(msg, process_native_word)


@cancel_fsm
def process_native_word(message):
    load_cache[message.chat.id].append(message.text)
    msg = bot.reply_to(message, "Send to me the group name for this word, or leave empty for default group")
    bot.register_next_step_handler(msg, process_group)


@cancel_fsm
def process_group(message):
    group = message.text.strip() if message.text.strip() != "" else "default"
    load_cache[message.chat.id].append(group)
    # Assume db.input_words now accepts three arguments: foreign, native, and group
    print(message.chat.id,
          load_cache[message.chat.id][0],
          load_cache[message.chat.id][2],
          group,
          load_cache[message.chat.id][1])
    db.input_words(message.chat.id,
                   load_cache[message.chat.id][0],
                   load_cache[message.chat.id][2],
                   group,
                   load_cache[message.chat.id][1])
    load_cache.pop(message.chat.id)
    bot.send_message(message.chat.id, "The word has been added successfully!")


# -------------------------------
# Exporting words (/upload)
# -------------------------------
@bot.message_handler(commands=['upload'])
def upload_words(message):
    msg = bot.reply_to(message, "Choose export format: txt, csv, or json")
    bot.register_next_step_handler(msg, upload_words_format)


def upload_words_format(message):
    data = db.get_show_words(message.chat.id)  # Expecting list of tuples: (foreign, native, group)
    fmt = message.text.lower()
    if fmt == 'txt':
        filename = f'{message.chat.id}.txt'
        with open(filename, 'w', encoding='utf-8') as file:
            for line in data:
                file.write(f"{line[0]} --- {line[1]} (Group: {line[2]})\n")
        bot.send_document(message.chat.id, open(filename, 'rb'))
    elif fmt == 'csv':
        filename = f'{message.chat.id}.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Foreign", "Native", "Group"])
            for line in data:
                writer.writerow([line[0], line[1], line[2]])
        bot.send_document(message.chat.id, open(filename, 'rb'))
    elif fmt == 'json':
        filename = f'{message.chat.id}.json'
        words_list = [{"foreign": line[0], "native": line[1], "group": line[2]} for line in data]
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(words_list, file, ensure_ascii=False, indent=2)
        bot.send_document(message.chat.id, open(filename, 'rb'))
    else:
        bot.send_message(message.chat.id, "Unsupported format. Please choose txt, csv, or json.")


# -------------------------------
# Showing words (/show)
# -------------------------------
@bot.message_handler(commands=['show'])
def show_words(message):
    # data = db.output_words(message.chat.id)
    # msg_text = "Your words:\n"
    # show_cache[message.chat.id] = {}
    # for i, line in enumerate(data, 1):
    #     show_cache[message.chat.id][i] = line  # each line: (foreign, native, group)
    #     msg_text += f"{i}. {line[0]} --- {line[1]} (Group: {line[2]}, Lang: {line[3]})\n"
    msg = bot.reply_to(message,
                       "What group do you want to see?\n"
                       "If you want to see multiple groups just write them separating by ', '(comma and space)\n"
                       "If you want to see all groups write 'all'")
    bot.register_next_step_handler(msg, process_group_show)


@cancel_fsm
def process_group_show(message):
    groups = message.text.split(", ")
    if groups == ["all"]:
        show_cache[message.chat.id] = {"groups": []}
    else:
        show_cache[message.chat.id] = {"groups": [message.text.split(", ")]}
    msg = bot.reply_to(message,
                       "What languages do you want to see?\n"
                       "If you want to see multiple langs just write them separating by ', '(comma and space)\n"
                       "If you want to see all lang write 'all'")
    bot.register_next_step_handler(msg, final_show)


@cancel_fsm
def final_show(message):
    langs = message.text.split(", ")
    if langs == ["all"]:
        show_cache[message.chat.id]["langs"] = []
    else:
        show_cache[message.chat.id]["langs"] = langs
    data = db.get_show_words(message.chat.id, show_cache[message.chat.id]["groups"], show_cache[message.chat.id]["langs"])
    msg_text = "Your words:\n"
    for line in data:
        msg_text += f"{line[0]}  --  {line[1]} \n    Group: {line[2]}, Lang: {line[3]}\n"
    bot.send_message(message.chat.id, msg_text)


# -------------------------------
# Editing words (/edit)
# -------------------------------
@bot.message_handler(commands=['edit'])
def edit_words(message):
    msg = bot.reply_to(message, "Write word in native language and foreign lang code (separated by space)")
    bot.register_next_step_handler(msg, select_edit_word)


@cancel_fsm
def select_edit_word(message):
    try:
        native, lang = message.text.split(" ")
        edit_cache[message.chat.id] = [native, lang]
    except (TypeError, KeyError, ValueError):
        msg = bot.reply_to(message,
                           'You need to write two words: word in native and lang code\nFor example: (target ru)')
        bot.register_next_step_handler(msg, edit_words)
        return
    edit_cache[message.chat.id] = db.get_word_for_editing(message.chat.id, native, lang)[0]
    if not edit_cache[message.chat.id]:
        msg = bot.reply_to(message, "There are no any words with this pair of native word and lang!")
        bot.register_next_step_handler(msg, select_edit_word)
    else:
        markup = InlineKeyboardMarkup(row_width=3)
        markup.add(
            InlineKeyboardButton('Delete', callback_data='edit_cb_del'),
            InlineKeyboardButton('Change', callback_data='edit_cb_change'),
            InlineKeyboardButton('Move', callback_data='edit_cb_move')
        )
        bot.send_message(message.chat.id, f'Editing word:\n{edit_cache[message.chat.id]}', reply_markup=markup)


def enter_foreign_change(message):
    db.change_foreign_word(message.chat.id,
                           edit_cache[message.chat.id][1],
                           message.text,
                           edit_cache[message.chat.id][3])
    bot.send_message(message.chat.id, "Foreign word has been changed!")
    edit_cache.pop(message.chat.id, None)


def enter_native_change(message):
    db.change_native_word(message.chat.id,
                          edit_cache[message.chat.id][1],
                          message.text,
                          edit_cache[message.chat.id][3])
    bot.send_message(message.chat.id, "Native word has been changed!")
    edit_cache.pop(message.chat.id, None)


def enter_group_change(message):
    db.change_native_word(message.chat.id,
                          edit_cache[message.chat.id][1],
                          message.text,
                          edit_cache[message.chat.id][3])
    bot.send_message(message.chat.id, "Group of word has been changed!")
    edit_cache.pop(message.chat.id, None)


def enter_lang_change(message):
    pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def callback_query(call):
    if call.data == 'edit_cb_del':
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton('Yes', callback_data='edit_del_y'),
                   InlineKeyboardButton('No', callback_data='edit_del_n'))
        bot.edit_message_text(f'Deleting word:\n{edit_cache[call.message.chat.id]}\nConfirm?', call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == 'edit_del_y':
        db.delete_words(call.message.chat.id, edit_cache[call.message.chat.id][0])
        bot.send_message(call.message.chat.id, "Word deleted successfully.")
        edit_cache.pop(call.message.chat.id, None)
        show_words(call.message)
    elif call.data == 'edit_del_n':
        bot.send_message(call.message.chat.id, "Deletion cancelled.")
    elif call.data == "edit_cb_change":  # Change word info
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton('Change foreign', callback_data='edit_change_fgn'),
                   InlineKeyboardButton('Change native', callback_data='edit_change_ntv'),
                   InlineKeyboardButton('Change group', callback_data='edit_change_grp'),
                   InlineKeyboardButton('Change lang code', callback_data='edit_change_lng'))
        bot.edit_message_text(f"Choose what to change:\n{edit_cache[call.message.chat.id]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=markup)
    elif call.data == "edit_change_fgn":  # Change foreign word
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Back", callback_data='edit_cb_change'))
        bot.edit_message_text(call.message.text + "\nEnter new foreign word:",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=markup)
        bot.register_next_step_handler(call.message, enter_foreign_change)
    elif call.data == "edit_change_ntv":  # Change native word
        bot.edit_message_text(call.message.text + "\nEnter new native word:", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, enter_native_change)
    elif call.data == "edit_change_grp":  # Change native word
        bot.edit_message_text("Enter new group:", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, enter_group_change)
    elif call.data == "edit_change_lng":  # Change native word
        bot.edit_message_text("Enter new lang code:", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, enter_lang_change)
    elif call.data == "edit_cb_move":
        bot.edit_message_text("Enter new group for this word:", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, enter_move)


# -------------------------------
# Sorting words (/sort)
# -------------------------------
def sort_words(message):
    sort_by = message.text.lower()
    data = db.get_show_words(message.chat.id)
    if sort_by == 'en':
        sorted_data = sorted(data, key=lambda x: x[0])
    elif sort_by == 'ru':
        sorted_data = sorted(data, key=lambda x: x[1])
    else:
        bot.send_message(message.chat.id, "Invalid sort option. Use 'en' or 'ru'.")
        return
    msg_text = "Sorted words:\n"
    for i, line in enumerate(sorted_data, 1):
        msg_text += f"{i}. {line[0]} --- {line[1]} (Group: {line[2]})\n"
    bot.send_message(message.chat.id, msg_text)


# -------------------------------
# Flashcards (/flash)
# -------------------------------
@bot.message_handler(commands=['flash'])
def flashcards_command(message):
    start_flashcards(message)


def start_flashcards(message):
    data = db.get_show_words(message.chat.id)
    if not data:
        bot.send_message(message.chat.id, "No words available for flashcards.")
        return
    flash_cache[message.chat.id] = {"words": data, "index": 0}
    word = flash_cache[message.chat.id]["words"][0]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Show Answer", callback_data="flash_show"))
    bot.send_message(message.chat.id, f"Flashcard:\nWord: {word[0]}\nWhat is the translation?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("flash_"))
def flash_callback(call):
    chat_id = call.message.chat.id
    if call.data == "flash_show":
        index = flash_cache[chat_id]["index"]
        word = flash_cache[chat_id]["words"][index]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Next", callback_data="flash_next"))
        bot.edit_message_text(f"Flashcard:\nWord: {word[0]}\nTranslation: {word[1]}", chat_id, call.message.message_id, reply_markup=markup)
    elif call.data == "flash_next":
        flash_cache[chat_id]["index"] = (flash_cache[chat_id]["index"] + 1) % len(flash_cache[chat_id]["words"])
        index = flash_cache[chat_id]["index"]
        word = flash_cache[chat_id]["words"][index]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Show Answer", callback_data="flash_show"))
        bot.edit_message_text(f"Flashcard:\nWord: {word[0]}\nWhat is the translation?", chat_id, call.message.message_id, reply_markup=markup)


# -------------------------------
# Reminders (/setreminder)
# -------------------------------
@bot.message_handler(commands=['setreminder'])
def set_reminder_command(message):
    msg = bot.reply_to(message, "Enter the group for which to set a reminder (or type 'all'):")
    bot.register_next_step_handler(msg, process_reminder_group)


def process_reminder_group(message):
    group = message.text.strip().lower()
    reminder_cache[message.chat.id] = {"group": group}
    msg = bot.reply_to(message, "Enter reminder interval in minutes:")
    bot.register_next_step_handler(msg, process_reminder_interval)


def process_reminder_interval(message):
    try:
        interval = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid interval. Please enter a number.")
        return
    reminder_cache[message.chat.id]["interval"] = interval
    bot.send_message(message.chat.id, f"Reminder set for group '{reminder_cache[message.chat.id]['group']}' every {interval} minutes.")
    schedule_reminder(message.chat.id, reminder_cache[message.chat.id]["group"], interval)


def schedule_reminder(chat_id, group, interval):
    def send_reminder():
        if group == "all":
            data = db.get_show_words(chat_id)
        else:
            # Assuming your database module has this function; otherwise, filter locally.
            data = db.get_words_by_group(chat_id, group)
        if data:
            msg_text = f"Reminder for group '{group}':\n"
            for i, line in enumerate(data, 1):
                msg_text += f"{i}. {line[0]} --- {line[1]}\n"
            bot.send_message(chat_id, msg_text)
        # Reschedule the reminder
        t = threading.Timer(interval * 60, send_reminder)
        t.start()
        reminder_timers[chat_id] = t

    t = threading.Timer(interval * 60, send_reminder)
    t.start()
    reminder_timers[chat_id] = t


# -------------------------------
# Start polling
# -------------------------------
bot.infinity_polling()

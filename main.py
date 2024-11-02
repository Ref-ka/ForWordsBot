import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import whisper
from database import DataBase
from os import remove
import config

TOKEN = config.TOKEN

bot = telebot.TeleBot(TOKEN)

db = DataBase()

load_cache = {}
upload_cache = {}
delete_cache = {}
edit_cache = {}

model = whisper.load_model("medium", device="cuda")
whisper.DecodingOptions(fp16=False)


@bot.message_handler(commands=['start'])
def send_instruction(message):
    bot.reply_to(message, 'Hi!\nI can help you in learning english language!\nFor now I can remember words which you '
                          'will input and make learning cards of these words.\nCommands: \\input_word, \\make cards')


@bot.message_handler(commands=['load'])
def start_input(message):
    msg = bot.reply_to(message, "Let's make a card!\nSend to me a word on english")
    bot.register_next_step_handler(msg, process_eng_word)


def process_eng_word(message):
    if message.chat.id not in load_cache:
        load_cache[message.chat.id] = []
    if message.text:
        load_cache[message.chat.id].append(message.text)
    elif message.voice.file_id:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(f'{message.chat.id}.ogg', 'wb') as file:
            file.write(downloaded_file)
        # model = whisper.load_model("base")
        # whisper.DecodingOptions(language='eng', fp16=False)
        load_cache[message.chat.id].append(model.transcribe(f'{message.chat.id}.ogg', language='en')['text'])
        remove(f'{message.chat.id}.ogg')

    msg = bot.reply_to(message, 'Send to me word on russian')
    bot.register_next_step_handler(msg, process_ru_word)


def process_ru_word(message):
    if message.text:
        load_cache[message.chat.id].append(message.text)
    elif message.voice.file_id:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(f'{message.chat.id}.ogg', 'wb') as file:
            file.write(downloaded_file)
        # model = whisper.load_model("base")
        # whisper.DecodingOptions(language='ru', fp16=False)
        load_cache[message.chat.id].append(model.transcribe(f'{message.chat.id}.ogg', language='ru')['text'])
        remove(f'{message.chat.id}.ogg')
    print(message.chat.id, load_cache[message.chat.id][0], load_cache[message.chat.id][1])
    print(type(message.chat.id), type(load_cache[message.chat.id][0]), type(load_cache[message.chat.id][1]))
    db.input_words(message.chat.id, load_cache[message.chat.id][0], load_cache[message.chat.id][1])
    load_cache.pop(message.chat.id)
    bot.reply_to(message, 'The word has loaded successfully!')


@bot.message_handler(commands=['upload'])
def upload_words(message):
    msg = bot.reply_to(message, "Choose format of uploaded words (txt, json, csv)")
    bot.register_next_step_handler(msg, upload_words_format)


def upload_words_format(message):
    data = db.output_words(message.chat.id)
    match message.text:
        case 'txt':
            print(data)
            with open(f'{message.chat.id}.txt', 'w', encoding='utf-8') as file:
                for line in data:
                    file.write(f"{' '.join(line)}\n")
            bot.send_document(message.chat.id, open(f'{message.chat.id}.txt', 'r'))


@bot.message_handler(commands=['delete'])
def delete_words(message):
    msg = bot.reply_to(message, "Write english words to delete (separated by space)")
    bot.register_next_step_handler(msg, delete_input_eng)


def delete_input_eng(message: telebot.types.Message):
    delete_cache[message.chat.id] = {'eng': [], 'ru': []}
    delete_cache[message.chat.id]['eng'] += message.text.split()
    msg = bot.reply_to(message, "Write russian words to delete (separated by space)")
    bot.register_next_step_handler(msg, delete_input_ru)


def delete_input_ru(message: telebot.types.Message):
    delete_cache[message.chat.id]['ru'] += message.text.split()
    db.delete_words(message.chat.id, delete_cache[message.chat.id])
    bot.reply_to(message, 'Words successfully deleted!')


@bot.message_handler(commands=['show'])
def show_words(message: telebot.types.Message):
    data = db.output_words(message.chat.id)
    msg = "Your words:\n"
    for i, line in enumerate(data, 1):
        if message.chat.id not in upload_cache:
            upload_cache[message.chat.id] = {i: [line[0], line[1]]}
        else:
            upload_cache[message.chat.id][i] = [line[0], line[1]]
        msg += f"{i}. {line[0]} --- {line[1]}\n"
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['edit'])
def edit_word(message: telebot.types.Message):
    msg = bot.reply_to(message, "Write word index from /show")
    bot.register_next_step_handler(msg, select_edit_option)


def select_edit_option(message: telebot.types.Message):
    try:
        print(upload_cache)
        edit_cache[message.chat.id] = upload_cache[message.chat.id][int(message.text)]
    except TypeError:
        msg = bot.reply_to(message, 'You entered wrong id! son of a &^@#%')
        bot.register_next_step_handler(msg, edit_word)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('delete', callback_data='edit_cb_del'),
                   InlineKeyboardButton('change', callback_data='edit_cb_change'))
        bot.send_message(message.chat.id,
                         f'Word for editing: \n{upload_cache[message.chat.id][int(message.text)]}',
                         reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'edit_cb_del':
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(InlineKeyboardButton('yes', callback_data='edit_del_y'),
                   InlineKeyboardButton('no', callback_data='edit_del_n'))
        print(call.message.chat.id)
        bot.edit_message_text(f'Deleting word: \n{edit_cache[call.message.chat.id]}\nConfirm?',
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=markup)
    elif call.data == 'edit_del_y':
        print(edit_cache)
        db.delete_words(call.message.chat.id, edit_cache[call.message.chat.id][0])
        show_words(call.message)


bot.infinity_polling()

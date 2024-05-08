import telebot
import whisper
from database import DataBase
from os import remove
import config

TOKEN = config.TOKEN

bot = telebot.TeleBot(TOKEN)

db = DataBase()

load_cache = {}
upload_cache = {}

model = whisper.load_model("small")
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
    db.load_words(message.chat.id, load_cache[message.chat.id][0], load_cache[message.chat.id][1])
    load_cache.pop(message.chat.id)
    bot.reply_to(message, 'The word has loaded successfully!')


@bot.message_handler(commands=['upload'])
def upload_words(message):
    msg = bot.reply_to(message, "Chose format of uploaded words (txt, json, csv)")
    bot.register_next_step_handler(msg, upload_words_format)


def upload_words_format(message):
    data = db.upload_words(message.chat.id)
    match message.text:
        case 'txt':
            print(data)
            with open(f'{message.chat.id}.txt', 'w', encoding='utf-8') as file:
                for line in data:
                    file.write(f"{' '.join(line)}\n")
            bot.send_document(message.chat.id, open(f'{message.chat.id}.txt', 'r'))


bot.infinity_polling()

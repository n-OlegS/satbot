import telebot
from telebot import TeleBot
from core import Core
from dotenv import load_dotenv
import sqlite3

import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if TOKEN is None:
    quit("No bot token specified")

bot = TeleBot("")
core = Core()


@bot.message_handler(commands=["ping"])
def pong(m: telebot.types.Message):
    bot.reply_to(m, "Pong!")


def send_question(m: telebot.types.Message):
    cq, q_path, rem_t = core.generate_question(m.from_user.id)

    text = f"Вопрос {cq}/44\n\nОтправьте букву чтобы ответить или цифру, чтобы перейти на другой вопрос"

    bot.send_photo(m.chat.id, open(q_path, 'rb'), caption=text)


@bot.message_handler(commands=['start_test'])
def start_test(m):
    code = core.start_test(m.from_user.id)

    if code == 1:
        bot.reply_to(m, "Тест уже в процессе")
    elif code == 2:
        bot.reply_to(m, "Тест уже пройден")

    else:
        send_question(m)

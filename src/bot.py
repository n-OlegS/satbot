import telebot
from telebot import TeleBot
from core import Core, QUESTION_NUM
from dotenv import load_dotenv
import sqlite3
import threading
import time

import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
USER_EXPIRE_INTERVAL = 15

if TOKEN is None:
    quit("No bot token specified")
if ADMIN_ID is None:
    quit("No admin ID specified")

ADMIN_ID = int(ADMIN_ID)

bot = TeleBot(TOKEN)
core = Core()


@bot.message_handler(commands=["ping"])
def pong(m: telebot.types.Message):
    bot.reply_to(m, "Pong!")


timer_event = threading.Event()


def expire_user(uid):
    core.finish_test(uid)
    bot.send_message(uid, "Время вышло! Тест завершён.")


def check_timers():
    while True:
        timer_event.wait()
        for uid in core.get_expired_users():
            expire_user(uid)
        if core.has_active_users():
            time.sleep(USER_EXPIRE_INTERVAL)
        else:
            timer_event.clear()


threading.Thread(target=check_timers, daemon=True).start()


def send_question(m: telebot.types.Message):
    result = core.generate_question(m.from_user.id)

    if result is None:
        return

    cq, q_path, rem_t = result

    if time.time() >= rem_t:
        expire_user(m.from_user.id)
        return

    text = f"Вопрос {cq}/44\n\nОтправьте букву чтобы ответить или цифру, чтобы перейти на другой вопрос"

    with open(q_path, 'rb') as f:
        bot.send_photo(m.chat.id, f, caption=text)


@bot.message_handler(commands=['start_test'])
def start_test(m):
    code = core.start_test(m.from_user.id)

    if code is None:
        bot.reply_to(m, "Вы не зарегистрированы. Обратитесь к преподавателю.")
    elif code == 1:
        bot.reply_to(m, "Тест уже в процессе")
    elif code == 2:
        bot.reply_to(m, "Тест уже пройден")

    else:
        timer_event.set()
        send_question(m)


@bot.message_handler(commands=['new_test'])
def new_test(m: telebot.types.Message):
    if m.from_user.id != ADMIN_ID:
        return

    core.new_test()
    bot.send_message(m.chat.id, "Новый тест создан. Все студенты сброшены.")


@bot.message_handler(commands=['finish_test'])
def finish_test(m: telebot.types.Message):
    uid = m.from_user.id

    if not core.is_active(uid):
        bot.reply_to(m, "У вас нет активного теста.")
        return

    core.finish_test(uid)
    bot.send_message(m.chat.id, "Тест завершён!")


@bot.message_handler(func=lambda m: True)
def handle_message(m: telebot.types.Message):
    uid = m.from_user.id

    if not core.is_active(uid):
        return

    text = m.text.strip().lower()

    if text in ('a', 'b', 'c', 'd'):
        core.answer_q(uid, text)
        send_question(m)
    elif text.isdigit():
        code = core.switch_q(uid, int(text))
        if code == 1:
            bot.reply_to(m, "Неверный номер вопроса. Введите число от 1 до 44.")
        else:
            send_question(m)
    else:
        bot.reply_to(m, "Отправьте букву (a, b, c или d) или номер вопроса (1-44).")


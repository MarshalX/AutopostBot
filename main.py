# coding=utf-8
import os

from dotenv import load_dotenv
load_dotenv()

import telebot


# bot = telebot.AsyncTeleBot(misc.bot_token)
bot = telebot.TeleBot(os.environ.get('bot_token'))


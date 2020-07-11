# coding=utf-8
import os

import telebot


# bot = telebot.AsyncTeleBot(misc.bot_token)
bot = telebot.TeleBot(os.environ.get('bot_token'))


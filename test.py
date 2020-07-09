import os

from dotenv import load_dotenv
load_dotenv()

import pymysql

import database as db
# print(os.environ.get('db_host'))
# print(os.getenv('db_host'))
# print(os.getenv('db_name'))
# print(os.getenv('db_password'))
# print(os.getenv('db_user'))
# print(os.getenv('bot_token') + ' tg bot')
# print(os.environ.get('db_host'))
# print(os.environ.get('bot_token')  + '  tg bot')
# print("ok?")

# db.add_group('-1001272562933', '157516431') #T0st3r group
db.add_group('-1001360731738', '157516431') #konfa
a = db.get_all_groups()
print(a)
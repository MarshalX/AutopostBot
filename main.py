import os

import logging
from time import sleep
from datetime import datetime

import telebot

import database as db
import telegram as tg
import vkontakte as vk


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


bot = telebot.TeleBot(os.environ.get('bot_token'))


def main():
    def get_and_convert_tg_id(g):
        try:
            return int(g['tg_id'])
        except ValueError:
            if not g['tg_id'].startswith('@'):
                g['tg_id'] = f'@{g["tg_id"]}'

            tg_id = bot.get_chat(g['tg_id']).id
            db.set_tg_id(g['id'], tg_id)

            return tg_id

    while True:
        groups = db.get_all_groups()

        try:
            posts = vk.get_posts_for_publication(groups)
            for post in posts:
                for group in groups:
                    if -group['vk_id'] == post['source_id']:
                        sleep(0.25)
                        tg_id = get_and_convert_tg_id(group)
                        try:
                            tg.send_post(tg_id, post)
                            db.set_last_post(tg_id, -group['vk_id'], post['post_id'])
                            logger.info(f'Post {post["post_id"]} into {tg_id}')
                        except Exception as e:
                            logger.error(e)
                            sleep(0.25)
        except Exception as e:
            logger.error(e)
            sleep(0.25)

        sleep(20)


if __name__ == '__main__':
    main()

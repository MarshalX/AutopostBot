import os
import logging
from time import sleep

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

        for group in groups:
            try:
                tg_id = get_and_convert_tg_id(group)

                vk_id = int(group['vk_id'])
                if vk_id:
                    vk_id = -vk_id

                sleep(2.5)

                post = vk.get_post_for_publication(tg_id, vk_id)
                if post:
                    tg.send_post(tg_id, post)
                    db.set_last_post(tg_id, vk_id, post['id'])
                    logger.info(f'Post {post["id"]} into {tg_id}')
            except Exception as e:
                logger.error(e)

        sleep(45)


if __name__ == '__main__':
    main()

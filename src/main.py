import os
from time import sleep

import telebot

from log import logger
import database as db
import telegram as tg
import vkontakte as vk

bot = telebot.TeleBot(os.environ.get('bot_token'))


def main():
    while True:
        groups = db.get_all_groups()
        logger.info(f'Fetch {len(groups)} groups')

        try:
            posts = vk.get_posts_for_publication(groups)
            logger.info(f'Fetch {len(posts)} posts')

            group_to_vk_id = {g['vk_id']: g for g in groups}
            for post in posts:
                group = group_to_vk_id[-post['source_id']]
                logger.info(f'Processing group {group["id"]}')

                sleep(0.25)
                tg_id = tg.get_and_convert_id(group)
                try:
                    tg.send_post(tg_id, post)
                    db.set_last_post(tg_id, group['vk_id'], post['post_id'])
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

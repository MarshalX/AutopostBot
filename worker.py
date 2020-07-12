# coding=utf-8
from time import sleep

import database as db
import vkontakte as vk
import telegram as tg
from main import bot

from datetime import datetime


def main():
    try:
        while True:
            groups = db.get_all_groups()

            for group in groups:
                tg_id = []
                if group['tg_id'].startswith('-', 0, 1):
                    tg_id.append(group['tg_id'])
                    tg_id.append(group['tg_id'])
                else:
                    chat = bot.get_chat(f'@'+group['tg_id'])
                    tg_id.append(chat.id)
                    tg_id.append(group['tg_id'])

                vk_id = group['vk_id']

                post = vk.get_post_for_publication(tg_id, vk_id)
                if post is not False:
                    print("Post {} in to {}".format(post['id'], tg_id[0]))
                    tg.send_post(tg_id[0], post)
                    db.set_last_post(tg_id[1], vk_id, post['id'])

            print((str(datetime.now())).split('.')[0])
            sleep(30)

    except Exception as e:
        print(e)

    print("ERROR!")


if __name__ == '__main__':
    main()

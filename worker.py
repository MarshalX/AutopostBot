# coding=utf-8
from time import sleep

import database as db
import vkontakte as vk
import telegram as tg

from datetime import datetime


def main():
    try:
        while True:
            groups = db.get_all_groups()

            for group in groups:
                tg_id = group['tg_id']
                vk_id = group['vk_id']

                post = vk.get_post_for_publication(tg_id, vk_id)

                if post is not False:
                    print("Post {} in to {}".format(post['id'], tg_id))
                    tg.send_post('@' + tg_id, post)
                #     db.set_last_post(tg_id, vk_id, post['id'])

            print((str(datetime.now())).split('.')[0])
            sleep(300)
    except Exception as e:
        print(e)

    print("ERROR!")


if __name__ == '__main__':
    main()

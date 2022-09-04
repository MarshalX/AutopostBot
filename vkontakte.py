import os
import logging
from time import sleep

import requests

import database as db
from main import bot

logger = logging.getLogger(__name__)

URL = 'https://api.vk.com/method/{}?access_token=vk1.a.bjC5qoHG1DcPh5aQuy9l1imIUoI3LQ3KreXTaUzZWh2RFmxk4GoFK30jihsiQsUsiIQRTcBmbbSgNuqwLyFWFEs2SQsg8B7aNenlXApBB9bQHNAMGGdcHpJgOORV9GQgFps0JcwT-XAQagKAkrTQ2iTU4RbuyVPOJ5UhfohLlH6ntF_6ClgtafCL9NyMaCOf'

HEADERS = {
    'Content-type': 'application/json',
    'Cache-control': 'no-cache'
}


def send(method, token=os.environ.get('vk_token'), **kwargs):
    kwargs['v'] = '5.120'

    try:
        params = '&'.join([f'{k}={v}' for k, v in kwargs.items()])
        url = URL.format(method, token, params)

        response = requests.get(url, headers=HEADERS).json()

        sleep(0.4)

        if 'error' in response:
            raise RuntimeError(response['error'])

        return response
    except Exception as e:
        logger.error(e)


def get_posts(groups, count=50):
    source_ids = []

    for group in groups:
        vk_id = -group['vk_id']
        source_ids.append(vk_id)

    response = send('newsfeed.get', source_ids=source_ids, count=count, filters='post')

    if not response:
        return

    return source_ids, [post for post in response['response']['items'][::-1]]


def post_filter(response):
    publication_posts = []

    vk_pubs = set(response[0])
    posts = response[1]

    for post in posts:

        if post['post_type'] == 'post' or post['type'] == 'post':
            for group in vk_pubs:

                if group == post['source_id']:
                    tg_id = get_and_convert_tg_id(db.get_group(-group))

                    if post.get('is_pinned', 0) or post.get('marked_as_ads', 0):
                        continue
                    if db.is_duplicate_post(tg_id, post['source_id'], post['post_id']):
                        continue

                    publication_posts.append(post)

    return publication_posts


def get_posts_for_publication(groups):
    return post_filter(get_posts(groups, 50))


def get_and_convert_tg_id(g):
    try:
        return int(g['tg_id'])
    except ValueError:
        if not g['tg_id'].startswith('@'):
            g['tg_id'] = f'@{g["tg_id"]}'

        tg_id = bot.get_chat(g['tg_id']).id
        db.set_tg_id(g['id'], tg_id)

        return tg_id


def get_video(videos):
    res = send('video.get', videos=videos)

    if not res:
        return

    files = {}
    for video in res['response']['items']:
        files = video['files']
        break

    for k, v in files.items():
        if k != 'external':
            return v

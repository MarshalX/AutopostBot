import os
from time import sleep

import requests

import database as db
from log import logger

URL = 'https://api.vk.com/method/{}?access_token={}&{}'
API_VERSION = '5.120'
HEADERS = {
    'Content-type': 'application/json',
    'Cache-control': 'no-cache'
}

DEFAULT_POST_COUNT = 100


def send(method, token=os.environ.get('vk_token'), **kwargs):
    kwargs['v'] = API_VERSION

    try:
        params = '&'.join([f'{k}={v}' for k, v in kwargs.items()])
        url = URL.format(method, token, params)

        response = requests.get(url, headers=HEADERS).json()

        sleep(0.4)  # гениальный (нет) обход необходимости писать очередь и умещаться в rate limiter vk api

        if 'error' in response:
            raise RuntimeError(response['error'])

        return response
    except Exception as e:
        logger.error(e)


def get_posts(groups, count=DEFAULT_POST_COUNT):
    source_ids = []

    for group in groups:
        vk_id = -group['vk_id']
        source_ids.append(vk_id)

    response = send('newsfeed.get', source_ids=source_ids, count=count, filters='post', max_photos=100, return_banned=1)

    if not response:
        return

    return source_ids, list(reversed(response['response']['items']))


def post_filter(response):
    vk_pubs = set(response[0])
    posts = response[1]

    publication_posts = []
    for post in posts:
        is_post = post['post_type'] == 'post' or post['type'] == 'post'
        if post['source_id'] in vk_pubs and is_post:
            from telegram import get_and_convert_id
            tg_id = get_and_convert_id(db.get_group(-post['source_id']))

            if post.get('is_pinned', 0) or post.get('marked_as_ads', 0):
                continue
            if db.is_duplicate_post(tg_id, -post['source_id'], post['post_id']):
                continue

            publication_posts.append(post)

    return publication_posts


def get_posts_for_publication(groups):
    return post_filter(get_posts(groups))


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

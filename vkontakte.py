import os
import logging
from time import sleep

import requests

import database as db

logger = logging.getLogger(__name__)

URL = 'https://api.vk.com/method/{}?access_token={}&{}'

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


def get_posts(vk_id, count):
    response = send('wall.get', owner_id=vk_id, count=count, filter='owner')
    if not response:
        return

    return [post for post in response['response']['items']]


def post_filter(tg_id, posts):
    for post in posts:
        if post.get('is_pinned', 0) or post.get('marked_as_ads', 0):
            continue
        if db.is_duplicate_post(tg_id, post['owner_id'], post['id']):
            continue
        return post


def get_post_for_publication(tg_id, vk_id):
    return post_filter(tg_id, get_posts(vk_id, 10)[::-1])


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

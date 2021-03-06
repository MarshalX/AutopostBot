import os
import logging
from time import sleep

import requests

import database as db
from main import bot

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


def construct(**kwargs):
    params = ','.join([f"'{k}':'{v}'" for k, v in kwargs.items()])
    method = "API.wall.get({" + params + "})"

    return method


def execute(groups, posts_count):
    code_line = 'return ['

    for group in groups:
        vk_id = -group['vk_id']
        code_line += construct(owner_id=vk_id, count=posts_count, filter='owner') + ', '

    code_line += '];'

    response = send('execute', code=code_line)

    if not response:
        return

    return response


def get_posts(groups, count):
    response = execute(groups, count)
    groups_num = len(response['response'])

    return [post for i in range(groups_num) for post in response['response'][i]['items'][::-1]]


def post_filter(groups, posts):
    publication_posts = []

    for post in posts:
        for group in groups:
            if -group['vk_id'] == post['owner_id']:
                tg_id = get_and_convert_tg_id(group)

                if post.get('is_pinned', 0) or post.get('marked_as_ads', 0):
                    continue
                if db.is_duplicate_post(tg_id, post['owner_id'], post['id']):
                    continue
                publication_posts.append(post)

    return publication_posts


def get_posts_for_publication(groups):
    return post_filter(groups, get_posts(groups, 6))


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

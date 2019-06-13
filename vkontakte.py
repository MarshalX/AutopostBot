# coding=utf-8
import os

import requests
import json

import database as db

from time import sleep

URL = "https://api.vk.com/method/{}?{}access_token={}"

headers = {
    'Content-type': 'application/json',
    'Cache-control': 'no-cache'
}


def send(method, token=os.environ.get('vk_token'), **kwargs):
    kwargs.update({'v': '5.0'})
    params = ""
    try:
        for key, value in kwargs.items():
            params += "{}={}&".format(key, value)

        r = requests.get(
            URL.format(method, params, token),
            headers=headers
        )

        result = json.loads(r.text)
        sleep(1)

        return check(result)
    except Exception as e:
        print(e)
        return False


def check(result):
    try:
        temp = result["error"]
        return False
    except KeyError:
        return result


def get_posts(vk_id, count):
    res = send("wall.get", owner_id=-1 * vk_id, count=count, filter='owner')
    posts = []

    if not res:
        return

    for post in res["response"]["items"]:
        posts.append(post)

    return posts


def post_filter(tg_id, posts):
    for post in posts:
        try:
            if post["is_pinned"] == 1:
                continue
        except KeyError:
            pass

        if post["marked_as_ads"] == 1:
            continue
        if post["id"] not in db.get_last_posts(tg_id, post["to_id"]):
            return post
        else:
            return False

    return False


def get_post_for_publication(tg_id, vk_id):
    posts = get_posts(vk_id, 10)

    return post_filter(tg_id, posts)


def get_video(videos):
    res = send("video.get", token=os.environ.get('vk_user_token'), videos=videos)
    files = []
    video_url = ''

    if not res:
        return

    for video in res['response']['items']:

        files = video['files']
        break

    for file in files:
        if file != 'external':
            video_url = files[file]
            break

    return video_url

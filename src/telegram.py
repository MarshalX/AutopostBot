import re
from collections.abc import Callable
from html import escape

import telebot

import database as db
import tgraph
import vkontakte as vk
from log import logger
from main import bot


def reraise_flood_wait(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            if 'Error code: 429' in str(e):
                raise e

            logger.error(e)

    return wrapper


def get_and_convert_id(group: db.RawData) -> int:
    try:
        return int(group['tg_id'])
    except ValueError:
        if not group['tg_id'].startswith('@'):
            group['tg_id'] = f'@{group["tg_id"]}'

        tg_id = reraise_flood_wait(bot.get_chat)(group['tg_id']).id

        db.set_tg_id(group['id'], tg_id)

        return tg_id


def send_post(tg_id: int, post: dict) -> None:
    text = escape(post['text'])

    for vk_link, name in re.findall(r'\[([^]|]*)\|([^]]*)]', text):
        text = text.replace(f'[{vk_link}|{name}]', f'<a href="https://vk.com/{vk_link}">{name}</a>')

    photos = []
    docs = []
    audios = []
    videos = []

    unknown_attachments_count = 0

    for attachment in post.get('attachments', []):
        try:
            attach_type = attachment['type']

            if attach_type == 'photo':
                photos.append(attachment[attach_type]['sizes'][-1]['url'])
            elif attach_type == 'audio':
                audios.append(
                    (
                        attachment[attach_type]['url'],
                        f"{attachment[attach_type]['artist']} - {attachment[attach_type]['title']}",
                    )
                )
            elif attach_type == 'doc' and attachment[attach_type]['ext'] == 'gif':
                docs.append((attachment[attach_type]['url'], int(attachment[attach_type]['size'])))
            elif attach_type == 'video':
                videos_data = f"{attachment[attach_type]['owner_id']}_{attachment[attach_type]['id']}"

                video_url = vk.get_video(videos_data)
                if video_url is not None:
                    videos.append(video_url)
            else:
                logger.warning(f'Unknown attachment type: {attach_type}')
                unknown_attachments_count += 1
        except KeyError as e:
            logger.error(e)

    if unknown_attachments_count:
        logger.warning(f'Unknown attachments count: {unknown_attachments_count}')

    # Отправка текста если отправляется пачка чего-то или нет attachments
    with_attachments = len(photos) + len(docs) + len(videos) + len(audios) != 0
    if text and not unknown_attachments_count and len(text) < 4095:
        if (with_attachments and len(text) > 1024) or not with_attachments:
            reraise_flood_wait(bot.send_message)(chat_id=tg_id, text=text, parse_mode='HTML')
            text = ""
    elif len(text) > 4095:
        text = text.replace('\n', '<br>')
        author = reraise_flood_wait(bot.get_chat)(tg_id).title

        preface = text.split('<br>')[0]
        if len(preface) > 256:
            preface = f'{preface.split(".")[0]}...'
            if len(preface) > 256:
                preface = 'Новая публикация'

        text = tgraph.post(preface, author, text)
        reraise_flood_wait(bot.send_message)(chat_id=tg_id, text=f'<a href="{text}">{preface}</a>', parse_mode='HTML')
        return

    # Отправка пачки GIF
    if len(docs) > 1:
        for id_ in range(len(docs)):
            if docs[id_][1] >= 20971520:
                txt = f'<a href="{docs[id_][0]}">&#8203;</a>{text}'
                reraise_flood_wait(bot.send_message)(tg_id, txt, parse_mode='HTML')
            else:
                reraise_flood_wait(bot.send_document)(chat_id=tg_id, caption=text, data=docs[id_][0], parse_mode='HTML')

    # Грузим альбом фото если там больше одной
    if 10 >= len(photos) > 1:
        media = [telebot.types.InputMediaPhoto(photos[0], caption=text, parse_mode='HTML')]
        for id_ in range(1, len(photos)):
            media.append(telebot.types.InputMediaPhoto(photos[id_]))

        reraise_flood_wait(bot.send_media_group)(tg_id, media)

    # Грузим альбом видео если там больше одного
    if 10 >= len(videos) > 1:
        media = [telebot.types.InputMediaVideo(videos[0], caption=text, parse_mode="HTML")]
        for id_ in range(1, len(videos)):
            # пробуем собрать альбом из видео
            try:
                media.append(telebot.types.InputMediaVideo(videos[id_]))
            except Exception as e:
                logger.error(e)

        # media может остаться пустым, также может вернуть ошибку от ТГ, например не удалось получить видос по url
        reraise_flood_wait(bot.send_media_group)(tg_id, media)

    # Если фотка одна, в зависимости от кол-ва текста выбираем способ отправки (прямой или обход)
    if len(photos) == 1:
        if len(text) <= 1024:
            reraise_flood_wait(bot.send_photo)(tg_id, photos[0], caption=text, parse_mode='HTML')
        else:
            text = '<a href="{}">&#8203;</a>{}'.format(photos[0], text)
            reraise_flood_wait(bot.send_message)(tg_id, text, parse_mode='HTML')

        text = ""

    # Если гифка одна, в зависимости от кол-ва текста и размера файла выбираем способ отправки
    if len(docs) == 1:
        if len(text) >= 200 or docs[0][1] >= 20971520:  # 20 MB
            text = f'<a href="{docs[0][0]}">&#8203;</a>{text}'
            reraise_flood_wait(bot.send_message)(tg_id, text, parse_mode='HTML')
        else:
            reraise_flood_wait(bot.send_document)(chat_id=tg_id, data=docs[0][0], caption=text, parse_mode='HTML')

        text = ""

    # Если видео одно, в зависимости от кол-ва текста выбираем способ отправки (прямой или обход)
    if len(videos) == 1:
        if len(text) < 200:
            reraise_flood_wait(bot.send_video)(tg_id, videos[0], caption=text, parse_mode='HTML')
        else:
            text = f'<a href="{videos[0]}">&#8203;</a>{text}'
            reraise_flood_wait(bot.send_message)(tg_id, text, parse_mode='HTML')

        text = ""

    # Отправка всех аудио с поста. Внизу из-за приоритета отправки
    for audio in audios:
        caption = f'[{audio[1]}]\n\n{text}'
        reraise_flood_wait(bot.send_audio)(chat_id=tg_id, audio=audio[0], caption=caption, parse_mode='HTML')

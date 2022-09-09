import re
from html import escape

import telebot

import database as db
import tgraph
import vkontakte as vk
from log import logger
from main import bot


def get_and_convert_id(group):
    try:
        return int(group['tg_id'])
    except ValueError:
        if not group['tg_id'].startswith('@'):
            group['tg_id'] = f'@{group["tg_id"]}'

        tg_id = bot.get_chat(group['tg_id']).id

        db.set_tg_id(group['id'], tg_id)

        return tg_id


def send_post(group, post):
    text = post['text']

    text = escape(text)

    for vk_link, name in re.findall(r'\[([^]|]*)\|([^]]*)]', text):
        text = text.replace(f'[{vk_link}|{name}]', f'<a href="https://vk.com/{vk_link}">{name}</a>')

    photos = []
    docs = []
    audios = []
    videos = []

    another = 0

    try:
        for attachment in post.get('attachments', []):
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
                another += 1
    except KeyError as e:
        logger.error(e)

    # Отправка текста если отправляется пачка чего-то или нет attachments
    with_attachments = len(photos) + len(docs) + len(videos) + len(audios) != 0
    if text and not another and len(text) < 4095:
        if (with_attachments and len(text) > 1024) or not with_attachments:
            try:
                bot.send_message(chat_id=group, text=text, parse_mode='HTML')
            except:
                pass

            text = ""
    elif len(text) > 4095:
        text = text.replace("\n", '<br>')
        author = bot.get_chat(group).title

        preface = text.split("<br>")[0]
        if len(preface) > 256:
            preface = preface.split(".")[0] + "..."
            if len(preface) > 256:
                preface = "Новая публикация"

        text = tgraph.post(preface, author, text)
        bot.send_message(chat_id=group, text=f'<a href="{text}">{preface}</a>', parse_mode='HTML')
        return

    # Отправка пачки GIF
    if len(docs) > 1:
        for id_ in range(0, len(docs)):
            try:
                if docs[id_][1] >= 20971520:
                    txt = '<a href="{}">&#8203;</a>{}'.format(docs[id_][0], text)
                    bot.send_message(group, txt, parse_mode='HTML')
                else:
                    bot.send_document(chat_id=group, caption=text, data=docs[id_][0], parse_mode='HTML')
            except:
                pass

    # Грузим альбом фото если там больше одной
    if (len(photos) <= 10) and (len(photos) > 1):
        media = [telebot.types.InputMediaPhoto(photos[0], caption=text, parse_mode='HTML')]
        for id_ in range(1, len(photos)):
            media.append(telebot.types.InputMediaPhoto(photos[id_]))

        bot.send_media_group(group, media)

    # Грузим альбом видео если там больше одного
    if (len(videos) <= 10) and (len(videos) > 1):
        media = [telebot.types.InputMediaVideo(videos[0], caption=text, parse_mode="HTML")]
        for id_ in range(1, len(videos)):
            # пробуем собрать альбом из видео
            try:
                media.append(telebot.types.InputMediaVideo(videos[id_]))
            except Exception as e:
                logger.error(e)
            continue

        # media может остаться пустым, также может вернуть ошибку от ТГ, например не удалось получить видос по url
        try:
            bot.send_media_group(group, media)
        except Exception as e:
            logger.e(e)

    # Если фотка одна, в зависимости от кол-ва текста выбираем способ отправки (прямой или обход)
    if len(photos) == 1:
        if len(text) <= 1024:
            bot.send_photo(group, photos[0], caption=text, parse_mode='HTML')
        else:
            text = '<a href="{}">&#8203;</a>{}'.format(photos[0], text)
            bot.send_message(group, text, parse_mode='HTML')

        text = ""

    # Если гифка одна, в зависимости от кол-ва текста выбираем способ отправки (прямой или обход)
    if len(docs) == 1:
        if len(text) < 200:
            try:
                if docs[0][1] >= 20971520:
                    text = '<a href="{}">&#8203;</a>{}'.format(docs[0][0], text)
                    bot.send_message(group, text, parse_mode='HTML')
                else:
                    bot.send_document(chat_id=group, data=docs[0][0], caption=text, parse_mode='HTML')
            except:
                pass
        else:
            text = '<a href="{}">&#8203;</a>{}'.format(docs[0][0], text)
            bot.send_message(group, text, parse_mode='HTML')

        text = ""

    # Если видео одно, в зависимости от кол-ва текста выбираем способ отправки (прямой или обход)
    if len(videos) == 1:
        if len(text) < 200:
            try:
                bot.send_video(group, videos[0], caption=text, parse_mode='HTML')
            except:
                pass
        else:
            text = f'<a href="{videos[0]}">&#8203;</a>{text}'
            bot.send_message(group, text, parse_mode='HTML')

        text = ""

    # Отправка всех аудио с поста. Внизу из-за приоритета отправки
    for id_ in range(0, len(audios)):
        try:
            caption = f'[{audios[id_][1]}]\n\n{text}'
            bot.send_audio(chat_id=group, audio=audios[id_][0], caption=caption, parse_mode='HTML')
        except:
            pass

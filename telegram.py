# coding=utf-8
import re

import main
import vkontakte as vk

import telebot


def send_post(group, post):
    text = post['text']

    for vk_link, name in re.findall(r"\[([^\]|]*)\|([^\]]*)\]", text):
        text = text.replace(f'[{vk_link}|{name}]', f'<a href="https://vk.com/{vk_link}">{name}</a>')

    text = text.replace('<br>', '\n')

    photos = []
    docs = []
    audios = []
    videos = []

    another = 0

    try:
        for attachment in post['attachments']:
            type = attachment['type']

            if type == 'photo':
                for k, v in attachment[type].items():
                    if k.startswith('sizes'):
                        photos.append(attachment[type]['sizes'][-1]['url'])
            elif type == 'audio':
                audios.append((attachment[type]['url'], attachment[type]['artist'] + ' - ' + attachment[type]['title']))
            elif (type == 'doc') and (attachment[type]['ext'] == 'gif'):
                docs.append((attachment[type]['url'], int(attachment[type]['size'])))
            elif type == 'video':
                videos_data = '{}_{}'.format(attachment[type]['owner_id'], attachment[type]['id'])
                video_url = vk.get_video(videos_data)
                if video_url is not None:
                    videos.append(video_url)
            else:
                another += 1
    except KeyError as e:
        print(e)

    # Отправка текста если отправляется пачка чего-то или нет аттачей
    if (text is not None) and (text != "") and (another == 0):
        if (len(photos) > 1) or \
                (len(docs) > 1) or \
                (len(videos) > 1) or \
                (len(docs) == 0 and len(photos) == 0) and (len(videos) == 0):
            main.bot.send_message(chat_id=group, text=text, parse_mode='HTML')

            text = ""

    # Отправка пачки гифок
    if len(docs) > 1:
        for id in range(0, len(docs)):
            print(docs[id][1])
            if docs[id][1] >= 20971520:
                text = '<a href="{}">&#8203;</a>{}Test'.format(docs[id][0], text)
                main.bot.send_message(group, text, parse_mode='HTML')
            else:
                main.bot.send_document(chat_id=group, data=docs[id][0])

    # Грузим кучу ФОТОК если там больше одной
    if (len(photos) <= 10) and (len(photos) > 1):
        media = []

        for id in range(0, len(photos)):
            media.append(telebot.types.InputMediaPhoto(photos[id]))

        main.bot.send_media_group(group, media)

    # Грузим кучу ВИДОСОВ если там больше одной
    if (len(videos) <= 10) and (len(videos) > 1):
        media = []

        for id in range(0, len(videos)):
            media.append(telebot.types.InputMediaVideo(videos[id]))

        main.bot.send_media_group(group, media)

    # Если фотка одна, в зависимости от кол-ва текста выбираем способ отправки (прямой или обход)
    if len(photos) == 1:
        if len(text) < 200:
            main.bot.send_photo(group, photos[0], caption=text, parse_mode='HTML')
        else:
            text = '<a href="{}">&#8203;</a>{}'.format(photos[0], text)
            main.bot.send_message(group, text, parse_mode='HTML')

        text = ""

    # Если гифка одна, в зависимости от кол-ва текста выбираем способ отправки (прямой или обход)
    if len(docs) == 1:
        if len(text) < 200:
            try:
                if docs[0][1] >= 20971520:
                    text = '<a href="{}">&#8203;</a>{}'.format(docs[0][0], text)
                    main.bot.send_message(group, text, parse_mode='HTML')
                else:
                    main.bot.send_document(chat_id=group, data=docs[0][0], caption=text, parse_mode='HTML')
                # main.bot.send_document(group, docs[0], caption=text)
            except:
                pass
        else:
            text = '<a href="{}">&#8203;</a>{}'.format(docs[0][0], text)
            main.bot.send_message(group, text, parse_mode='HTML')

        text = ""

    # Если видео одно, в зависимости от кол-ва текста выбираем способ отправки (прямой или обход)
    if len(videos) == 1:
        if len(text) < 200:
            try:
                main.bot.send_video(group, videos[0], caption=text, parse_mode='HTML')
                # main.bot.send_document(group, videos[0], caption=text)
            except:
                pass
        else:
            text = '<a href="{}">&#8203;</a>{}'.format(videos[0], text)
            main.bot.send_message(group, text, parse_mode='HTML')

        text = ""

    # Отправка всех аудио с поста. Внизу из-за приоритета отправки
    for id in range(0, len(audios)):
        try:
            main.bot.send_audio(chat_id=group, audio=audios[id][0], caption=audios[id][1])
        except:
            pass

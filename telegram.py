import re

import telebot

import vkontakte as vk
from main import bot


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
        for attachment in post.get('attachments', []):
            type = attachment['type']

            if type == 'photo':
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
        if (((len(photos) > 1) or (len(docs) > 1) or (len(videos) > 1)) and (len(text) > 200)) or \
                (len(docs) == 0 and len(photos) == 0) and (len(videos) == 0):
            bot.send_message(chat_id=group, text=text, parse_mode='HTML')

            text = ""

    # Отправка пачки гифок
    if len(docs) > 1:
        for id_ in range(0, len(docs)):
            print(docs[id_][1])
            if docs[id_][1] >= 20971520:
                txt = '<a href="{}">&#8203;</a>{}'.format(docs[id_][0], text)
                bot.send_message(group, txt, parse_mode='HTML')
            else:
                bot.send_document(chat_id=group, caption=text, data=docs[id_][0])

    # Грузим кучу ФОТОК если там больше одной
    if (len(photos) <= 10) and (len(photos) > 1):
        media = []

        media.append(telebot.types.InputMediaPhoto(photos[0], caption=text))
        for id_ in range(1, len(photos)):
            media.append(telebot.types.InputMediaPhoto(photos[id_]))

        bot.send_media_group(group, media)

    # Грузим кучу ВИДОСОВ если там больше одного
    if (len(videos) <= 10) and (len(videos) > 1):
        media = []

        media.append(telebot.types.InputMediaVideo(videos[0], caption=text))
        for id_ in range(1, len(videos)):
            # пробуем собрать альбом из видосов
            try:
                media.append(telebot.types.InputMediaVideo(videos[id_]))
            except Exception as e:
                print(e)
            continue
        # media может остаться пустым, также может вернуть ошибку от ТГ, например не удалось получить видос по url
        try:
            bot.send_media_group(group, media)
        except Exception as e:
            print(e)

    # Если фотка одна, в зависимости от кол-ва текста выбираем способ отправки (прямой или обход)
    if len(photos) == 1:
        if len(text) < 200:
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
                # bot.send_document(group, docs[0], caption=text)
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
                # bot.send_document(group, videos[0], caption=text)
            except:
                pass
        else:
            text = '<a href="{}">&#8203;</a>{}'.format(videos[0], text)
            bot.send_message(group, text, parse_mode='HTML')

        text = ""

    # Отправка всех аудио с поста. Внизу из-за приоритета отправки
    for id_ in range(0, len(audios)):
        try:
            bot.send_audio(chat_id=group, audio=audios[id_][0], caption=audios[id_][1])
        except:
            pass

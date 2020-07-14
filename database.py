import os

import pymysql


def get_connection():
    return pymysql.connect(
        host=os.environ.get('db_host'),
        user=os.environ.get('db_user'),
        password=os.environ.get('db_password'),
        database=os.environ.get('db_name'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def is_duplicate_post(tg_id, vk_id, post_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            query = '''
                SELECT
                    COUNT(*)
                FROM
                    `groups`
                WHERE
                    `vk_id`= %s AND
                    `tg_id`= %s AND
                    `pre_last_post` != %s AND
                    `last_post` != %s AND
                    `last_post` < %s
            '''
            cursor.execute(query, (vk_id*-1, tg_id, post_id, post_id, post_id))

            return cursor.fetchone()['COUNT(*)'] == 0
    finally:
        connection.close()


def set_last_post(tg_id, vk_id, last_post):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            query = 'UPDATE `groups` SET `pre_last_post` = `last_post` WHERE `vk_id`= %s AND `tg_id`= %s'
            cursor.execute(query, (vk_id*-1, tg_id))

        connection.commit()

        with connection.cursor() as cursor:
            query = 'UPDATE `groups` SET `last_post` = %s WHERE `vk_id`= %s AND `tg_id`= %s'
            cursor.execute(query, (last_post, vk_id*-1, tg_id))

        connection.commit()
    finally:
        connection.close()


def get_group(vk_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT `*` FROM `groups` WHERE `vk_id` = %s', vk_id)

            return cursor.fetchone()
    finally:
        connection.close()


def get_all_groups():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT `*` FROM `groups`')

            return cursor.fetchall()
    finally:
        connection.close()


def set_tg_id(group_id, tg_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            query = 'UPDATE `groups` SET `tg_id` = %s WHERE `id`= %s'
            cursor.execute(query, (tg_id, group_id))

        connection.commit()
    finally:
        connection.close()

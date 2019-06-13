# coding=utf-8
import os

import pymysql


def get_connection():
    connection = pymysql.connect(os.environ.get('db_host'),
                                 user=os.environ.get('db_user'),
                                 password=os.environ.get('db_password'),
                                 database=os.environ.get('db_name'),
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def get_last_post(tg_id, vk_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `last_post` FROM `groups` WHERE `vk_id`=%s AND `tg_id`=%s"
            cursor.execute(sql, (vk_id * -1, tg_id))
            result = cursor.fetchone()

            return result['last_post']
    finally:
        connection.close()


def set_last_post(tg_id, vk_id, last_post):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE `groups` SET `last_post` = %s WHERE `vk_id`=%s AND `tg_id`=%s"
            cursor.execute(sql, (last_post, vk_id, tg_id))

        connection.commit()
    finally:
        connection.close()


def get_group(group):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `*` FROM `groups` WHERE `vk_id`=%s"
            cursor.execute(sql, group)
            result = cursor.fetchone()

            return result
    finally:
        connection.close()


def get_all_groups():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `*` FROM `groups`"
            cursor.execute(sql)
            result = cursor.fetchall()

            return result
    finally:
        connection.close()


def add_group(tg_id, vk_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO `groups` (`tg_id`, `vk_id`) VALUES (%s, %s)"
            cursor.execute(sql, (tg_id, vk_id))

        connection.commit()
    finally:
        connection.close()

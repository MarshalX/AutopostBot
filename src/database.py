import os
import sqlite3

RawData = dict[str, any]


def get_connection() -> sqlite3.Connection:
    con = sqlite3.connect(os.environ.get('db_path', 'db.sqlite'))
    # https://stackoverflow.com/a/41956666/8032027
    con.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
    return con


def is_duplicate_post(tg_id: str, vk_id: int, post_id: int) -> bool:
    with get_connection() as con:
        cur = con.cursor()

        query = '''
            SELECT
                COUNT(*)
            FROM
                `groups`
            WHERE
                `vk_id`= ? AND
                `tg_id`= ? AND
                `pre_last_post` != ? AND
                `last_post` != ? AND
                `last_post` < ?
        '''
        cur.execute(query, (vk_id, tg_id, post_id, post_id, post_id))

        return cur.fetchone()['COUNT(*)'] == 0


def set_last_post(tg_id: str, vk_id: int, last_post: int) -> None:
    with get_connection() as con:
        query = 'UPDATE `groups` SET `pre_last_post` = `last_post` WHERE `vk_id`= ? AND `tg_id`= ?'
        con.execute(query, (vk_id, tg_id))

        query = 'UPDATE `groups` SET `last_post` = ? WHERE `vk_id`= ? AND `tg_id`= ?'
        con.execute(query, (last_post, vk_id, tg_id))


def add_group(tg_id: str, vk_id: int) -> None:
    with get_connection() as con:
        con.execute('INSERT INTO groups(tg_id, vk_id) VALUES (?, ?)', (tg_id, vk_id))


def get_group(vk_id: int) -> RawData:
    with get_connection() as con:
        cur = con.cursor()
        cur.execute('SELECT * FROM `groups` WHERE `vk_id` = ?', (vk_id,))
        return cur.fetchone()


def get_all_groups() -> list[RawData]:
    with get_connection() as con:
        cur = con.cursor()
        cur.execute('SELECT * FROM `groups`')

        return cur.fetchall()


def set_tg_id(group_id: int, tg_id: str) -> None:
    with get_connection() as con:
        query = 'UPDATE `groups` SET `tg_id` = ? WHERE `id`= ?'
        con.execute(query, (tg_id, group_id))


if __name__ == '__main__':
    # simple tests for migration from MySQL to sqlite

    test_tg_id = '-1001245'
    test_tg_id2 = '-100678'
    test_vk_id = 1245
    test_post_id = 100
    test_post_id2 = 101

    def drop_all() -> None:
        con = get_connection()
        con.cursor().execute('DELETE FROM groups WHERE id > 0')
        con.commit()

    drop_all()

    add_group(test_tg_id, test_vk_id)
    group = get_group(test_vk_id)
    assert group['tg_id'] == test_tg_id
    set_tg_id(group['id'], test_tg_id2)
    assert get_group(test_vk_id)['tg_id'] == test_tg_id2

    all_groups = get_all_groups()
    assert len(all_groups) == 1
    assert all_groups[0]['id'] == group['id']

    set_last_post(test_tg_id2, test_vk_id, test_post_id)
    assert is_duplicate_post(test_tg_id2, test_vk_id, test_post_id)
    assert not is_duplicate_post(test_tg_id2, test_vk_id, test_post_id2)

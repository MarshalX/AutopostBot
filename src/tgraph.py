import os

from telegraph import Telegraph

telegraph = Telegraph()
telegraph.create_account(short_name=os.environ.get('telegraph', 'Telegraph'))


def post(name, author, text):
    response = telegraph.create_page(name, html_content=text, author_name=author)

    return 'http://telegra.ph/{}'.format(response['path'])

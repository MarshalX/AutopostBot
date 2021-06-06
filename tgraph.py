from telegraph import Telegraph


telegraph = Telegraph()
telegraph.create_account(short_name='1337')


def post(name, author, text):
    response = telegraph.create_page(name, html_content=text, author_name=author)

    return 'http://telegra.ph/{}'.format(response['path'])

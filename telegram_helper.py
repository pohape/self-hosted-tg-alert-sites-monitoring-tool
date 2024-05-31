import json
import time

import requests

from console_helper import Color, color_text


def id_bot(config):
    color_text('To see your user ID, go to Telegram and start the bot, and to view the ID of a message source, '
               'forward a message from a group/channel or another user.', Color.WARNING)
    last_update_id = None

    while True:
        updates = get_updates(config['telegram_bot_token'], last_update_id)

        if not updates['ok']:
            color_text('Telegram error: ' + str(updates), Color.ERROR)
            exit()
        elif 'result' in updates and updates['result']:
            for update in updates['result']:
                message = update.get('message')

                if message:
                    handle_message(config['telegram_bot_token'], message)
                    last_update_id = update['update_id'] + 1
        time.sleep(0.1)


def test_notifications(config, get_uniq_chat_ids):
    # Collect all unique chat IDs
    chat_ids = set()

    for site in config['sites'].values():
        chat_ids.update(get_uniq_chat_ids(site['tg_chats_to_notify']))

    # Send test message to each chat
    test_message = escape_special_chars('This is a test message from the monitoring script.')

    for chat_id in chat_ids:
        send_message(config['telegram_bot_token'], chat_id, test_message)


def escape_special_chars(text):
    special_chars = [
        '\\',
        '_',
        '~',
        '`',
        '>',
        '<',
        '&',
        '#',
        '+',
        '-',
        '=',
        '|',
        '{',
        '}',
        '.',
        '!',
        '$',
        '@',
        '[',
        ']',
        '(',
        ')',
        '^',
    ]

    text = str(text)

    for special_char in special_chars:
        text = text.replace(special_char, '\\' + special_char)

    return text


def send_message(bot_token, chat_id, message):
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(bot_token)

    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2"
    }

    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )

    response_parsed = response.json()

    if response_parsed['ok']:
        color_text(f"A message sent to {chat_id} successfully:", Color.SUCCESS)
        color_text(message, Color.QUOTATION)

        return None
    else:
        color_text(f"Failed to send test message to {chat_id}: {response_parsed['description']}", Color.ERROR)

        return response_parsed['description']


def get_updates(telegram_bot_token, offset=None):
    params = {'timeout': 100, 'offset': offset}
    response = requests.get(f'https://api.telegram.org/bot{telegram_bot_token}/getUpdates', params=params)

    return response.json()


def handle_message(bot_token, message):
    chat_id = message['chat']['id']

    if 'forward_from' in message:
        forwarded_user_id = message['forward_from']['id']
        response_text = f'The ID of the forwarded user is `{forwarded_user_id}`'
    elif 'forward_origin' in message:
        if message['forward_origin']['type'] == 'hidden_user':
            response_text = f'No can do: forwarded from a hidden user'
        else:
            forwarded_chat_id = message['forward_origin']['chat']['id']
            response_text = f'The ID of the forwarded chat is `{forwarded_chat_id}`'
    else:
        user_id = message['from']['id']
        response_text = f'Your user ID is `{user_id}`'

    send_message(bot_token, chat_id, response_text)

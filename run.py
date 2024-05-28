import json
import os
import time
import yaml
import requests
import argparse
from enum import Enum
from datetime import datetime
from croniter import croniter

config_file_name = 'config.yaml'


class RequestMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    HEAD = 'HEAD'


def perform_request(url: str, method: RequestMethod, search_string: str = '', timeout: int = 5, post_data: str = None):
    try:
        if method == RequestMethod.GET:
            response = requests.get(url, timeout=timeout)
        elif method == RequestMethod.POST:
            response = requests.post(url, data=post_data, timeout=timeout)
        elif method == RequestMethod.HEAD:
            response = requests.head(url, timeout=timeout)
        else:
            return "Invalid request method."

        response.raise_for_status()  # Raise an error for bad status codes

        # Only search for the string if it's a GET or POST request
        if method in {RequestMethod.GET, RequestMethod.POST} and search_string and search_string not in response.text:
            return f"Search string '{search_string}' not found in the response."

        return None

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"


def should_run(schedule: str) -> bool:
    base_time = datetime.now().replace(second=0, microsecond=0)
    cron = croniter(schedule, base_time)

    return cron.get_prev(datetime) == base_time or cron.get_next(datetime) == base_time


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


def tg_bot_send_message(bot_token, chat_id, message):
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
        return None
    else:
        return response_parsed['description']


def get_updates(telegram_bot_token, offset=None):
    params = {'timeout': 100, 'offset': offset}
    response = requests.get(f'https://api.telegram.org/bot{telegram_bot_token}/getUpdates', params=params)

    return response.json()


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run site monitoring script.')
    parser.add_argument('--telegram-test',
                        action='store_true',
                        help='Test sending messages to all Telegram chats found in the config file')
    parser.add_argument('--telegram-id-bot',
                        action='store_true',
                        help='A bot that replies with the user ID  using long polling')
    args = parser.parse_args()

    # Load the configuration file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file_name)

    if not os.path.isfile(config_path):
        exit(config_path + ' not found')

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    if args.telegram_test:
        telegram_test(config)
    elif args.telegram_id_bot:
        telegram_id_bot(config)
    else:
        process_each_site(config)


def telegram_id_bot(config):
    last_update_id = None

    while True:
        updates = get_updates(config['telegram_bot_token'], last_update_id)

        if not updates['ok']:
            print('Telegram error:')
            exit(updates)
        elif 'result' in updates and updates['result']:
            for update in updates['result']:
                message = update.get('message')

                if message:
                    chat_id = message['chat']['id']
                    user_id = message['from']['id']
                    response_text = f'Your user ID is `{user_id}`'

                    print(response_text)

                    tg_bot_send_message(config['telegram_bot_token'], chat_id, response_text)
                    last_update_id = update['update_id'] + 1
        time.sleep(0.1)


def telegram_test(config):
    # Collect all unique chat IDs
    chat_ids = set()

    for site in config['sites'].values():
        chat_ids.update(site.get('tg_chats_to_notify', []))

    # Send test message to each chat
    test_message = escape_special_chars('This is a test message from the monitoring script.')

    for chat_id in chat_ids:
        result = tg_bot_send_message(config['telegram_bot_token'], chat_id, test_message)

        if result:
            print(f"Failed to send test message to {chat_id}: {result}")
        else:
            print(f"Test message sent to {chat_id} successfully.")


def process_each_site(config):
    for site_name, site in config['sites'].items():
        url = site['url']
        method = RequestMethod[site['method']]
        search_string = site.get('search_string', '')
        timeout = site['timeout']
        schedule = site.get('schedule', '* * * * *')
        post_data = site.get('post_data', None)
        tg_chats_to_notify = site.get('tg_chats_to_notify', [])

        if should_run(schedule):
            error_message = perform_request(url, method, search_string, timeout, post_data)

            if error_message:
                error_message = error_message.strip()
                print('Error for {}: {}'.format(site_name, error_message))

                for chat_id in tg_chats_to_notify:
                    error_message_for_tg = 'Error for *{}*: ```\n{}\n```'.format(
                        escape_special_chars(site_name),
                        error_message
                    )

                    tg_sending_error = tg_bot_send_message(config['telegram_bot_token'], chat_id, error_message_for_tg)

                    if tg_sending_error:
                        print(f"Failed to send message to {chat_id}: {tg_sending_error}")
            else:
                print(f"Request to {site_name} completed successfully.")


if __name__ == "__main__":
    main()

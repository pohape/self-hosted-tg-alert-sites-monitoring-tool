import json
import os
import yaml
import requests
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


def main():
    # Load the configuration file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file_name)

    if not os.path.isfile(config_path):
        exit(config_path + ' not found')

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    bot_token = config['telegram_bot_token']

    # Process each site in the configuration
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
                for chat_id in tg_chats_to_notify:
                    error_message_for_tg = 'Error for *{}*: ```\n{}\n```'.format(
                        escape_special_chars(site_name),
                        error_message.strip()
                    )

                    print(error_message_for_tg)
                    tg_sending_error = tg_bot_send_message(bot_token, chat_id, error_message_for_tg)

                    if tg_sending_error:
                        print(f"Failed to send message to {chat_id}: {tg_sending_error}")
            else:
                print(f"Request to {site_name} completed successfully.")


if __name__ == "__main__":
    main()

import argparse
import os
from datetime import datetime
from enum import Enum

import requests
import yaml
from croniter import croniter

import telegram_helper

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


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run site monitoring script.')
    parser.add_argument('--telegram-test',
                        action='store_true',
                        help='Test sending messages to all Telegram chats found in the config file')
    parser.add_argument('--telegram-id-bot',
                        action='store_true',
                        help='A bot that replies with the user ID using long polling')
    parser.add_argument('--force',
                        action='store_true',
                        help='Force check all sites immediately, regardless of the schedule')
    args = parser.parse_args()

    # Load the configuration file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file_name)

    if not os.path.isfile(config_path):
        exit(config_path + ' not found')

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    if args.telegram_test:
        telegram_helper.test(config)
    elif args.telegram_id_bot:
        telegram_helper.id_bot(config)
    else:
        process_each_site(config, force=args.force)


def process_each_site(config, force=False):
    for site_name, site in config['sites'].items():
        url = site['url']
        method = RequestMethod[site['method']]
        search_string = site.get('search_string', '')
        timeout = site['timeout']
        schedule = site.get('schedule', '* * * * *')
        post_data = site.get('post_data', None)
        tg_chats_to_notify = site.get('tg_chats_to_notify', [])

        if force or should_run(schedule):
            error_message = perform_request(url, method, search_string, timeout, post_data)

            if error_message:
                error_message = error_message.strip()
                print('Error for {}: {}'.format(site_name, error_message))

                for chat_id in tg_chats_to_notify:
                    error_message_for_tg = 'Error for *{}*: ```\n{}\n```'.format(
                        telegram_helper.escape_special_chars(site_name),
                        error_message
                    )

                    telegram_helper.send_message(config['telegram_bot_token'], chat_id, error_message_for_tg)
            else:
                print(f"Request to {site_name} completed successfully.")


if __name__ == "__main__":
    main()

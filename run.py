import argparse
import os
from datetime import datetime
from enum import Enum

import requests
import yaml
from croniter import croniter

import telegram_helper

CONFIG_FILE_NAME = 'config.yaml'
DEFAULT_SCHEDULE = '* * * * *'
DEFAULT_TIMEOUT = 5
DEFAULT_METHOD = 'GET'
DEFAULT_STATUS_CODE = 200


class RequestMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    HEAD = 'HEAD'


class Color(Enum):
    RED = 91
    YELLOW = 93
    GREEN = 92


def perform_request(url: str, method: RequestMethod, status_code: int, search: str, timeout: int, post_data: str):
    try:
        if method == RequestMethod.GET:
            response = requests.get(url, timeout=timeout)
        elif method == RequestMethod.POST:
            response = requests.post(url, data=post_data, timeout=timeout)
        elif method == RequestMethod.HEAD:
            response = requests.head(url, timeout=timeout)
        else:
            return "Invalid request method."

        if response.status_code != status_code:
            return f"Expected status code '{status_code}', but got '{response.status_code}'"

        # Only search for the string if it's a GET or POST request
        if method in {RequestMethod.GET, RequestMethod.POST} and search and search not in response.text:
            return f"Search string '{search}' not found in the response."

        return None

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"


def should_run(schedule: str) -> bool:
    base_time = datetime.now().replace(second=0, microsecond=0)
    cron = croniter(schedule, base_time)

    return cron.get_prev(datetime) == base_time or cron.get_next(datetime) == base_time


def color_text(text, color: Color):
    print(f"\033[{color.value}m{text}\033[0m")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run site monitoring script.')
    parser.add_argument('--test-notifications',
                        action='store_true',
                        help='Test sending messages to all Telegram chats found in the config file')
    parser.add_argument('--id-bot-mode',
                        action='store_true',
                        help='A bot that replies with the user ID using long polling')
    parser.add_argument('--force',
                        action='store_true',
                        help='Force check all sites immediately, regardless of the schedule')
    args = parser.parse_args()

    # Load the configuration file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE_NAME)

    if not os.path.isfile(config_path):
        exit(config_path + ' not found')

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    if args.test_notifications:
        telegram_helper.test_notifications(config)
    elif args.id_bot_mode:
        telegram_helper.id_bot(config)
    else:
        process_each_site(config, force=args.force)


def process_each_site(config, force=False):
    for site_name, site in config['sites'].items():
        if force or should_run(site.get('schedule', DEFAULT_SCHEDULE)):
            error_message = perform_request(
                url=site['url'],
                method=RequestMethod[site.get('method', DEFAULT_METHOD)],
                status_code=site.get('status_code', DEFAULT_STATUS_CODE),
                search=site.get('search_string', ''),
                timeout=site.get('timeout', DEFAULT_TIMEOUT),
                post_data=site.get('post_data', None)
            )

            if error_message:
                error_message = error_message.strip()
                print('Error for {}: {}'.format(site_name, error_message))

                for chat_id in site.get('tg_chats_to_notify', []):
                    error_message_for_tg = 'Error for *{}*: ```\n{}\n```'.format(
                        telegram_helper.escape_special_chars(site_name),
                        error_message
                    )

                    telegram_helper.send_message(config['telegram_bot_token'], chat_id, error_message_for_tg)
            else:
                print(f"Request to {site_name} completed successfully.")


if __name__ == "__main__":
    main()

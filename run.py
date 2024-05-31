import argparse
import os
from datetime import datetime
from enum import Enum

import requests
import yaml
from croniter import croniter, CroniterBadCronError, CroniterBadDateError

import telegram_helper

CONFIG_FILE_NAME = 'config.yaml'
REQUIRED_FIELDS = ['url', 'tg_chats_to_notify']
DEFAULT = {
    'timeout': 5,
    'schedule': '* * * * *',
    'method': 'GET',
    'status_code': 200,
    'post_data': None,
    'search_string': '',
}


class RequestMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    HEAD = 'HEAD'


class Color(Enum):
    BOLD = 1
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


def check_config(config):
    report = {}

    for site_name, site in config['sites'].items():
        report[site_name] = {
            Color.RED: {},
            Color.YELLOW: {},
            Color.GREEN: {},
        }

        for field_name in REQUIRED_FIELDS:
            if field_name not in site:
                report[site_name][Color.RED][field_name] = 'required field not found, you need to add it'
            elif field_name == 'tg_chats_to_notify':
                lst = site[field_name]

                if not isinstance(lst, list):
                    report[site_name][Color.RED][field_name] = 'must be a list of at least one chat ID'
                elif not all(isinstance(i, int) or (isinstance(i, str) and i.isdigit()) for i in lst) or not lst:
                    report[site_name][Color.RED][field_name] = 'chat IDs must contain only digits'
        for field_name in site:
            if field_name not in REQUIRED_FIELDS and field_name not in DEFAULT:
                report[site_name][Color.YELLOW][field_name] = 'unknown field, ignored'

        for field_name in DEFAULT:
            if field_name in site:
                if field_name == 'schedule' and not is_valid_cron(site['schedule']):
                    report[site_name][Color.RED][field_name] = f"invalid cron syntax: '{site['schedule']}'"
                else:
                    report[site_name][Color.GREEN][field_name] = site[field_name]
            else:
                report[site_name][Color.YELLOW][field_name] = f"not found, default value is '{DEFAULT[field_name]}'"

    print_check_config_report(report)


def print_check_config_report(report):
    for site_name, fields in report.items():
        color_text(f"\n=== {site_name} ===", Color.BOLD)
        for color, field_info in fields.items():
            for field_name, message in field_info.items():
                color_text(f"  {field_name}: {message}", color)


def is_valid_cron(schedule: str) -> bool:
    try:
        croniter(schedule)

        return True
    except (CroniterBadCronError, CroniterBadDateError):
        return False


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
    parser.add_argument('--check-config',
                        action='store_true',
                        help='Check configuration for each site and display missing or default values')
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
    elif args.check_config:
        check_config(config)
    else:
        process_each_site(config, force=args.force)


def process_each_site(config, force=False):
    for site_name, site in config['sites'].items():
        if force or should_run(site.get('schedule', DEFAULT['schedule'])):
            error_message = perform_request(
                url=site['url'],
                method=RequestMethod[site.get('method', DEFAULT['method'])],
                status_code=site.get('status_code', DEFAULT['status_code']),
                search=site.get('search_string', DEFAULT['search_string']),
                timeout=site.get('timeout', DEFAULT['timeout']),
                post_data=site.get('post_data', DEFAULT['post_data'])
            )

            if error_message:
                error_message = error_message.strip()
                print('Error for {}: {}'.format(site_name, error_message))

                for chat_id in site['tg_chats_to_notify']:
                    error_message_for_tg = 'Error for *{}*: ```\n{}\n```'.format(
                        telegram_helper.escape_special_chars(site_name),
                        error_message
                    )

                    telegram_helper.send_message(config['telegram_bot_token'], chat_id, error_message_for_tg)
            else:
                print(f"Request to {site_name} completed successfully.")


if __name__ == "__main__":
    main()

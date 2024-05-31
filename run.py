import argparse
import os
from datetime import datetime
from enum import Enum

import requests
import yaml
from croniter import croniter, CroniterBadCronError, CroniterBadDateError

import telegram_helper
from console_helper import Color, color_text

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


def check_chat_id_validity(chat_id):
    return isinstance(chat_id, int) or (isinstance(chat_id, str) and chat_id.lstrip('-').isdigit())


def get_uniq_chat_ids(chat_ids):
    return set(map(str, chat_ids))


def check_config(config):
    report = {}

    for site_name, site in config['sites'].items():
        report[site_name] = {
            Color.ERROR: {},
            Color.WARNING: {},
            Color.SUCCESS: {},
        }

        for field_name in REQUIRED_FIELDS:
            if field_name not in site:
                report[site_name][Color.ERROR][field_name] = 'required field not found, you need to add it'
            elif field_name == 'tg_chats_to_notify':
                chat_id_list = site[field_name]

                if not isinstance(chat_id_list, list):
                    report[site_name][Color.ERROR][field_name] = 'must be a list of at least one chat ID'
                elif not all(check_chat_id_validity(chat_id) for chat_id in chat_id_list) or not chat_id_list:
                    report[site_name][Color.ERROR][field_name] = 'chat IDs must contain only digits'
                else:
                    report[site_name][Color.SUCCESS][field_name] = ', '.join(get_uniq_chat_ids(chat_id_list))
            else:
                report[site_name][Color.SUCCESS][field_name] = site[field_name]
        for field_name in site:
            if field_name not in REQUIRED_FIELDS and field_name not in DEFAULT:
                report[site_name][Color.WARNING][field_name] = 'unknown field, ignored'

        for field_name in DEFAULT:
            if field_name in site:
                if field_name == 'schedule' and not is_valid_cron(site['schedule']):
                    report[site_name][Color.ERROR][field_name] = f"invalid cron syntax: '{site['schedule']}'"
                elif field_name == 'method':
                    method_upper = site[field_name].upper()

                    if not any(method_upper == item.value for item in RequestMethod):
                        report[site_name][Color.ERROR][field_name] = f"invalid method syntax: '{method_upper}'"
                    else:
                        report[site_name][Color.SUCCESS][field_name] = method_upper
                else:
                    report[site_name][Color.SUCCESS][field_name] = site[field_name]
            else:
                report[site_name][Color.WARNING][field_name] = f"not found, default value is '{DEFAULT[field_name]}'"

    print_check_config_report(report)


def print_check_config_report(report):
    for site_name, fields in report.items():
        color_text(f"\n=== {site_name} ===", Color.TITLE)
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
        telegram_helper.test_notifications(config, get_uniq_chat_ids)
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
                method=RequestMethod[site.get('method', DEFAULT['method']).upper()],
                status_code=site.get('status_code', DEFAULT['status_code']),
                search=site.get('search_string', DEFAULT['search_string']),
                timeout=site.get('timeout', DEFAULT['timeout']),
                post_data=site.get('post_data', DEFAULT['post_data'])
            )

            if error_message:
                error_message = error_message.strip()
                color_text('Error for {}: {}'.format(site_name, error_message), Color.ERROR)

                for chat_id in get_uniq_chat_ids(site['tg_chats_to_notify']):
                    error_message_for_tg = 'Error for *{}*: ```\n{}\n```'.format(
                        telegram_helper.escape_special_chars(site_name),
                        error_message
                    )

                    telegram_helper.send_message(config['telegram_bot_token'], chat_id, error_message_for_tg)
            else:
                color_text(f"Request to {site_name} completed successfully.", Color.SUCCESS)


if __name__ == "__main__":
    main()

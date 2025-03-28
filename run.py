import argparse
import os
import socket
import ssl
from datetime import datetime, timezone
from enum import Enum
from urllib.parse import urlparse

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
    'headers': {},
    'follow_redirects': False,
}


class RequestMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    HEAD = 'HEAD'


certificate_cache = {}


def get_certificate_expiry_with_cache(hostname: str, port: int = 443) -> dict:
    cache_key = '{}:{}'.format(hostname, port)

    if cache_key not in certificate_cache:
        certificate_cache[cache_key] = get_certificate_expiry(hostname, port)

    return certificate_cache[cache_key]


def get_certificate_expiry(hostname: str, port: int = 443) -> dict:
    try:
        context = ssl.create_default_context()

        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        not_before = datetime.strptime(cert['notBefore'], "%b %d %H:%M:%S %Y GMT")
        not_after = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y GMT")

        return {
            'issuer': cert['issuer'],
            'not_before': not_before,
            'not_after': not_after,
            'is_valid': not_before <= datetime.now(tz=timezone.utc) <= not_after,
            'error': None
        }
    except Exception as e:
        return {
            'issuer': None,
            'not_before': None,
            'not_after': None,
            'is_valid': None,
            'error': str(e)
        }


def get_server_info():
    hostname = socket.gethostname()
    hostname_escaped = telegram_helper.escape_special_chars(hostname)

    return f"```SERVER\n{hostname_escaped} ({socket.gethostbyname(hostname)})```"


def generate_curl_command(url: str,
                          follow_redirects: bool,
                          method: RequestMethod,
                          timeout: int,
                          post_data: str = None,
                          headers: dict = None):
    header_options = ' '.join([f"-H '{key}: {value}'" for key, value in headers.items()]) if headers else ''
    base = f"curl --max-time {timeout} -v{' ' + header_options if header_options else ''} '{url}'"

    if follow_redirects:
        base += ' -L'

    if method == RequestMethod.HEAD:
        return f"{base} --head"
    elif method == RequestMethod.POST and post_data:
        return f"{base} -X POST -d '{post_data}'"
    elif method != RequestMethod.GET:
        return f"{base} -X {method.value}"

    return base


def error(err: str,
          site_name: str,
          url: str,
          follow_redirects: bool,
          method: RequestMethod,
          timeout: int,
          post_data: str = None,
          headers: dict = None):
    return '_{}_:\n*{}*\n\n{}\n\n{}\n```sh\n{}```'.format(
        telegram_helper.escape_special_chars(site_name),
        telegram_helper.escape_special_chars(err),
        get_server_info(),
        'To replicate the request, you can use the following cURL command:',
        generate_curl_command(url, follow_redirects, method, timeout, post_data, headers)
    ).strip()


def perform_request(site_name: str,
                    url: str,
                    follow_redirects: bool,
                    method: RequestMethod,
                    status_code: int,
                    search: str,
                    timeout: int,
                    post_data: str,
                    headers: dict):
    if url.startswith('https://'):
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        cert = get_certificate_expiry_with_cache(hostname, parsed_url.port if parsed_url.port else 443)

        if cert['error']:
            return error(f"SSL certificate error: {cert['error']}",
                         site_name=site_name,
                         url=url,
                         follow_redirects=follow_redirects,
                         method=method,
                         timeout=timeout,
                         post_data=post_data,
                         headers=headers)
        elif not cert['is_valid']:
            return error(f"SSL certificate has expired or is not yet valid: {cert['not_before']} - {cert['not_after']}",
                         site_name=site_name,
                         url=url,
                         follow_redirects=follow_redirects,
                         method=method,
                         timeout=timeout,
                         post_data=post_data,
                         headers=headers)

    try:
        if method == RequestMethod.GET:
            res = requests.get(url, timeout=timeout, headers=headers, allow_redirects=follow_redirects)
        elif method == RequestMethod.POST:
            res = requests.post(url, timeout=timeout, headers=headers, allow_redirects=follow_redirects, data=post_data)
        elif method == RequestMethod.HEAD:
            res = requests.head(url, timeout=timeout, headers=headers, allow_redirects=follow_redirects)
        else:
            return error('Invalid request method.',
                         site_name=site_name,
                         url=url,
                         follow_redirects=follow_redirects,
                         method=method,
                         timeout=timeout,
                         post_data=post_data,
                         headers=headers)

        if res.status_code != status_code:
            return error(f"Expected status code '{status_code}', but got '{res.status_code}'",
                         site_name=site_name,
                         url=url,
                         follow_redirects=follow_redirects,
                         method=method,
                         timeout=timeout,
                         post_data=post_data,
                         headers=headers)

        # Only search for the string if it's a GET or POST request
        if method in {RequestMethod.GET, RequestMethod.POST} and search and search not in res.text:
            return error(f"The string '{search}' not found in the response.",
                         site_name=site_name,
                         url=url,
                         follow_redirects=follow_redirects,
                         method=method,
                         timeout=timeout,
                         post_data=post_data,
                         headers=headers)

        return None

    except requests.exceptions.RequestException as e:
        return error(f"An error occurred: {e}",
                     site_name=site_name,
                     url=url,
                     follow_redirects=follow_redirects,
                     method=method,
                     timeout=timeout,
                     post_data=post_data,
                     headers=headers)


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
            if field_name == 'post_data':
                method_is_post = site['method'].upper() == RequestMethod.POST.value if 'method' in site else False
                post_data_specified = 'post_data' in site

                if method_is_post and post_data_specified:
                    report[site_name][Color.SUCCESS][field_name] = site[field_name]
                elif method_is_post and not post_data_specified:
                    report[site_name][Color.WARNING][field_name] = 'the method is POST, but no post_data specified, '
                    report[site_name][Color.WARNING][field_name] += 'are you sure this is what you want?'
                elif not method_is_post and post_data_specified:
                    report[site_name][Color.WARNING][field_name] = 'ignored because the method is not POST'
            elif field_name == 'headers':
                if field_name in site:
                    if isinstance(site[field_name], dict):
                        headers_str = ', '.join([f'{k}: {v}' for k, v in site[field_name].items()])
                        report[site_name][Color.SUCCESS][field_name] = headers_str
                    else:
                        report[site_name][Color.ERROR][field_name] = 'must be a dictionary of header key-value pairs'
                else:
                    report[site_name][Color.WARNING][field_name] = 'not found, default value is empty headers'
            elif field_name in site:
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
                site_name=site_name,
                url=site['url'],
                follow_redirects=site.get('follow_redirects', DEFAULT['follow_redirects']),
                method=RequestMethod(site.get('method', DEFAULT['method']).upper()),
                status_code=site.get('status_code', DEFAULT['status_code']),
                search=site.get('search_string', DEFAULT['search_string']),
                timeout=site.get('timeout', DEFAULT['timeout']),
                post_data=site.get('post_data', DEFAULT['post_data']),
                headers=site.get('headers', DEFAULT['headers'])
            )

            if error_message:
                color_text(error_message, Color.ERROR)

                for chat_id in get_uniq_chat_ids(site['tg_chats_to_notify']):
                    telegram_helper.send_message(config['telegram_bot_token'], chat_id, error_message)
            else:
                color_text(f"Request to {site_name} completed successfully.", Color.SUCCESS)


if __name__ == "__main__":
    main()

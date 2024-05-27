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


def perform_request(url: str, method: RequestMethod, search_string: str = '', timeout: int = 5):
    try:
        if method == RequestMethod.GET:
            response = requests.get(url, timeout=timeout)
        elif method == RequestMethod.POST:
            response = requests.post(url, timeout=timeout)
        elif method == RequestMethod.HEAD:
            response = requests.head(url, timeout=timeout)
        else:
            return "Invalid request method."

        response.raise_for_status()  # Raise an error for bad status codes

        # Only search for the string if it's a GET or POST request
        if method in {RequestMethod.GET, RequestMethod.POST} and search_string not in response.text:
            return f"Search string '{search_string}' not found in the response."

        return None

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"


def should_run(schedule: str) -> bool:
    base_time = datetime.now().replace(second=0, microsecond=0)
    cron = croniter(schedule, base_time)

    return cron.get_prev(datetime) == base_time or cron.get_next(datetime) == base_time


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

    # Process each site in the configuration
    for site in config['sites']:
        url = site['url']
        method = RequestMethod[site['method']]
        search_string = site.get('search_string', '')
        timeout = site['timeout']
        schedule = site.get('schedule', '* * * * *')

        if should_run(schedule):
            result = perform_request(url, method, search_string, timeout)

            if result:
                print(f"Error for {url}: {result}")
            else:
                print(f"Request to {url} completed successfully.")


if __name__ == "__main__":
    main()

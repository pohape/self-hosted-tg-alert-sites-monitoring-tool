import os

import yaml
import requests
from enum import Enum

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
        print(response.text)

        # Only search for the string if it's a GET or POST request
        if method in {RequestMethod.GET, RequestMethod.POST} and search_string not in response.text:
            return f"Search string '{search_string}' not found in the response."

        return None

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"


def main():
    # Load the configuration file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = script_dir + '/' + config_file_name

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

        result = perform_request(url, method, search_string, timeout)

        if result:
            print(f"Error for {url}: {result}")
        else:
            print(f"Request to {url} completed successfully.")


if __name__ == "__main__":
    main()

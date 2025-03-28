## Self-hosted sites monitoring tool with Telegram alerts on errors
This is a self-hosted site monitoring tool that checks the availability of websites using GET, POST, and HEAD requests. The tool looks for a specified text on the monitored page, as defined in the configuration. It sends notifications to specified Telegram accounts (or channels/chats) and allows you to flexibly schedule monitoring tasks using a cron-like schedule.

### Features

- **Multiple HTTP Methods**: Supports GET, POST, and HEAD requests for monitoring website availability.
- **SSL Certificate Monitoring**: Automatically verifies the validity of HTTPS certificates, ensuring they are properly configured and up to date.
- **Custom Headers**: Allows the inclusion of custom HTTP headers in requests.
- **Content Validation**: Searches for specified text on the monitored page to ensure content validity.
- **Telegram Notifications**: Sends notifications to Telegram on errors.
- **Flexible Scheduling**: Schedule monitoring tasks using cron-like syntax.
- **Easy Configuration**: Customizable through a YAML configuration file.
- **Debug Modes**: Offers debug modes to effortlessly identify required Telegram chat IDs, debug Telegram API token configuration, and test everything without hassle.

### Quick start

##### 1. Clone the Repository and Install Dependencies

```shell
git clone https://github.com/pohape/self-hosted-tg-alert-sites-monitoring-tool
cd self-hosted-tg-alert-sites-monitoring-tool
pip3 install -r requirements.txt
```

##### 2. Create a new bot by chatting with [@BotFather](https://t.me/BotFather) on Telegram. Follow the instructions to obtain your bot token. Add the token to the configuration file:

```shell
echo "telegram_bot_token: '12345:SDGFFHWRE-EW3b16Q'" > config.yaml
```

##### 3. Run the script with the --id-bot-mode option to get your chat ID:

```shell
python3 run.py --id-bot-mode
```
Obtain your user or chat ID by sending a message to the bot or forwarding a message to the bot running in this mode. Then press <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop the bot.
##### 4. Update the config.yaml file with your bot token and add a site to monitor:

```yaml
telegram_bot_token: '12345:SDGFFHWRE-EW3b16Q'
sites:
  main_page:
    url: "https://example.com/"
    search_string: "Example Domain"
    tg_chats_to_notify:
      - '123456789'
```

##### 5. Check the configuration file for any missing or incorrect settings:

```shell
python3 run.py --check-config
```

This will validate the configuration for each site and display any issues.

##### 6. Test sending notifications to all Telegram chats specified in the configuration:

```shell
python3 run.py --test-notifications
```

This will send a test message to all chat IDs listed in the **tg_chats_to_notify** section of the configuration file.
You will see a full Telegram API error text if something won't succeed. In case of failure, the full Telegram API error
text will be shown, allowing you to debug easily.

##### 7. Run the script once manually to check all sites immediately:

```shell
python3 run.py --force
```

This will check all sites listed in the configuration file regardless of their schedule.

##### 8. Add the script to your crontab to run it every minute:

```shell
crontab -e
```

Add the following line:

```shell
* * * * * python3 /path/to/self-hosted-tg-alert-sites-monitoring-tool/run.py
```

### Usage

##### To run the script normally, simply execute:

```shell
python3 run.py
```

##### To test Telegram notifications:

```shell
python3 run.py --test-notifications
```

##### To start the Telegram bot that replies with user IDs using long polling:

```shell
python3 run.py --id-bot-mode
```

##### To force check all sites immediately:

```shell
python3 run.py --force
```
```diff
+ Request to home_page completed successfully.

- Error for not_found: Expected status code '404', but got '200'
+ A message with the error sent to 5487855 successfully
```

##### To check the configuration for any issues:

```shell
python3 run.py --check-config
```
```diff
@@ home_page @@
!  timeout: not found, default value is '5'
!  status_code: not found, default value is '200'
!  schedule: not found, default value is '* * * * *'
+  url: https://example.com/
+  tg_chats_to_notify: 5487855
+  method: GET
+  search_string: ENGLISH

@@ not_found @@
-  schedule: invalid cron syntax: '2 * * * '
+  url: https://example.com/qwerty
+  tg_chats_to_notify: -1831467, 5487855
+  timeout: 5
+  method: HEAD
+  status_code: 404
```

### Configuration

The configuration is done through the **config.yaml** file. Below is an example configuration:

```yaml
# Your Telegram Bot Token
telegram_bot_token: 'YOUR_TELEGRAM_BOT_TOKEN'

sites:
  # 1. GET request to the main page where we look for "<body>"
  #    - No timeout specified (default is 5 seconds)
  #    - No method specified (default is GET)
  main_page_check:
    url: "https://example.com/"
    follow_redirects: True # Redirects are not followed by default
    search_string: "<body>"
    # Notifications will be sent to the frontend group
    tg_chats_to_notify:
      - '1234567890'  # frontend group ID
    # Schedule: every minute (default)

  # 2. Explicit GET request to a non-existent page, expecting 404 and "Not Found"
  not_found_page_check:
    url: "https://example.com/nonexistent-page"
    follow_redirects: False # Redirects are not followed by default, making this the same as the default behavior.
    method: "GET"
    status_code: 404
    search_string: "Not Found"
    timeout: 2  # 2 seconds timeout
    # Notifications will be sent to the backend group
    tg_chats_to_notify:
      - '2345678901'  # backend group ID
    # Schedule: every 5 minutes
    schedule: '*/5 * * * *'  # Every 5 minutes

  # 3. POST request to the API with authorization and Content-Type JSON, expecting status_code = 201
  api_post_check:
    url: "https://example.com/api/endpoint"
    method: "POST"
    headers:
      Content-Type: 'application/json'
      Authorization: 'Bearer YOUR_API_TOKEN'
    post_data: '{"key": "value"}'
    status_code: 201
    timeout: 3  # 3 seconds timeout
    # Notifications will be sent to the API group and to the backend group
    tg_chats_to_notify:
      - '3456789012'  # API group ID
      - '2345678901'  # Backend group ID
    # Schedule: every 15 minutes
    schedule: '*/15 * * * *'  # Every 15 minutes

  # 4. Sending a contact form through POST request, as browsers typically do by default
  feedback_form_submission:
    url: "https://example.com/contact"
    method: "POST"
    headers:
      Content-Type: 'application/x-www-form-urlencoded'
    post_data: "name=John+Doe&email=john.doe%40example.com&message=Hello+World"
    status_code: 200
    search_string: "Thank you for your message"
    timeout: 2  # 2 seconds timeout
    # Notifications will be sent to the frontend group
    tg_chats_to_notify:
      - '1234567890'  # frontend group ID
    # Schedule: every day at midnight
    schedule: '0 0 * * *'  # Every day at 00:00

  # 5. HEAD request to privacy_policy.pdf to check resource availability
  privacy_policy_check:
    url: "https://example.com/privacy_policy.pdf"
    method: "HEAD"
    # Notifications will be sent to the backend group
    tg_chats_to_notify:
      - '2345678901'  # backend group ID
    # Schedule: every hour
    schedule: '0 * * * *'  # Every hour at 00 minutes
    # No timeout specified (default is 5 seconds)

  # 6. Monitor ChatGPT API balance availability (one check costs ~$0.000001275)
  chat_gpt_balance_check:
    url: "https://api.openai.com/v1/chat/completions"
    method: "POST"
    headers:
      Content-Type: 'application/json'
      Authorization: 'Bearer YOUR_OPENAI_API_KEY'
    post_data: '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Ping"}], "max_tokens": 1}'
    status_code: 200
    search_string: 'prompt_tokens'
    schedule: '0 * * * *'  # Every hour at 00 minutes
    tg_chats_to_notify:
      - '2345678999'  # infrastructure manager ID
```

- **telegram_bot_token**: Your Telegram bot token obtained from @BotFather.
- **sites**: A list of sites to monitor.
- **url**: The URL of the site to monitor.
- **follow_redirects**: (optional, default is False): Whether to follow HTTP redirects during the request.
- **method** (optional, default is GET): The HTTP method to use (GET, POST, HEAD).
- **headers** (optional): A dictionary of HTTP headers to include in the request.
- **post_data** (optional): Only for the POST method.
- **status_code** (optional, default is 200): An expected HTTP status code.
- **search_string** (optional): The string to search for in the response (for GET and POST requests).
- **timeout** (optional, default is 5): The timeout for the request in seconds.
- **schedule** (optional, default is '* * * * *'): The cron-like schedule for monitoring the site.
- **tg_chats_to_notify**: List of Telegram chat IDs to notify in case of an error.

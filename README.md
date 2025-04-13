# 🛡️ Self-hosted Uptime Monitor with Telegram Alerts

💬 Monitor your websites using **GET/POST/HEAD** requests, verify **SSL certificates**, and check for **specific content** — all configured via a simple YAML file.  
Get instant **Telegram alerts** after N failures and a recovery notification when the site is back online.  
**No cloud. No lock-in. No Docker. Just Python + crontab.**

---

### 🏠 Why Self-Hosted?

- ✅ Runs anywhere — no Docker or containers needed
- ✅ No third-party APIs or subscriptions
- ✅ Full control, full privacy

---

### 🔧 Perfect for:

- Internal tools & dashboards
- APIs that shouldn’t go unnoticed
- Low-cost uptime monitoring (no external services)

---

### 🚀 Features

- 🔁 **HTTP Methods**: GET, POST, HEAD
- 🔐 **SSL Certificate Expiry Checks**
- 🧠 **Content Validation**: Search for a string in the response
- 🛠️ **Custom Headers** & POST data
- 🕒 **Flexible Cron Scheduling** per site
- 💬 **Telegram Alerts** on errors & recovery
- ⚙️ **YAML-Based Config** — easy to read, edit, and version
- 🧪 **Debug/Test Modes** to simplify setup

---

### ⚡ Quick Start
Spin up your own uptime monitor with Telegram alerts in just a few steps:
##### 🔧 1. Clone the repo & install dependencies

```shell
git clone https://github.com/pohape/self-hosted-tg-alerts-uptime-monitor
cd self-hosted-tg-alerts-uptime-monitor
pip3 install -r requirements.txt
```

##### 🤖 2. Create a Telegram bot
Chat with [@BotFather](https://t.me/BotFather), create a new bot, and copy the token. Then create a **config.yaml** file:
```shell
echo "telegram_bot_token: '12345:SDGFFHWRE-EW3b16Q'" > config.yaml
```

##### 🆔 3. Get your Telegram chat ID
Start the bot in ID mode to find out your user/chat ID:
```shell
python3 run.py --id-bot-mode
```
➡️ Send any message to your bot, or forward a message from the group where you want to receive notifications.
🛠️ If you want to receive notifications in a group, make sure the bot has been added to that group.
✂️ Switch to the terminal and press <kbd>Ctrl</kbd>+<kbd>C</kbd> — your ID will appear in the terminal.

##### ✍️ 4. Add a site to monitor
Edit **config.yaml** and define your site(s):

```yaml
telegram_bot_token: 'YOUR_BOT_TOKEN_HERE'

sites:
  homepage:
    url: "https://example.com"
    search_string: "Example Domain"
    tg_chats_to_notify:
      - '123456789'  # your Telegram user or chat ID
```

##### 🧪 5. Validate the config
This will validate the configuration for each site and display any issues:
```shell
python3 run.py --check-config
```

##### 📬 6. Send a test notification
Make sure Telegram alerts work:
```shell
python3 run.py --test-notifications
```
You’ll get a test message in every listed chat — or a clear error if something’s wrong.

##### 🚀 7. Run a manual check (optional)
Force a one-time check of all sites:
```shell
python3 run.py --force
```

##### 🕒 8. Add to crontab
Run every minute using cron:
```shell
crontab -e
```

Add this line:
```shell
* * * * * python3 /path/to/self-hosted-tg-alerts-uptime-monitor/run.py
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
Example results:
```diff
+ Request to home_page completed successfully.

- Error for not_found: Expected status code '404', but got '200'
+ A message with the error sent to 5487855 successfully
```

##### To check the configuration for any issues:

```shell
python3 run.py --check-config
```
Example results:
```diff
@@ home_page @@
!  timeout: not found, default value is '5'
!  status_code: not found, default value is '200'
!  schedule: not found, default value is '* * * * *'
+  url: https://example.com/
+  tg_chats_to_notify: 5487855
+  notify_after_attempt: 3  # Notify only after 3 failed checks in a row
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
- **notify_after_attempt** (optional, default is 1): Number of consecutive failures required before a Telegram alert is sent. Helps to reduce false alarms from temporary glitches.

### 🔄 Smart Recovery Notifications

- 🚨 One alert after N consecutive failures (no spam or duplicate messages)
- 🔁 Continues checking once a minute during downtime (ignoring the original schedule temporarily)
- ✅ "Back online" message sent when site recovers, with:
  - Duration of downtime (in minutes)
  - Number of failed checks
- 📆 After recovery, monitoring returns to your custom schedule — fully automated.




## Self-hosted sites monitoring tool with Telegram alerts on errors
This is a self-hosted site monitoring tool that checks the availability of websites using GET, POST, and HEAD requests. The tool looks for a specified text on the monitored page, as defined in the configuration. It sends notifications to specified Telegram accounts (or channels/chats) and allows you to flexibly schedule monitoring tasks using a cron-like schedule.

### Features
- Supports GET, POST, and HEAD requests for monitoring website availability
- Searches for specified text on the monitored page to ensure content validity
- Sends notifications to Telegram on errors
- Flexible scheduling with cron-like syntax
- Customizable through a YAML configuration file
- Offers debug modes to effortlessly identify required Telegram chat IDs, debug Telegram API token configuration and test everything without hassle

### Quick start
##### 1. Clone the repository and install the required Python packages:
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
    method: "GET"
    search_string: "Example Domain"
    timeout: 5
    schedule: '* * * * *'
    tg_chats_to_notify:
      - '123456789'
```
##### 5. Test sending notifications to all Telegram chats specified in the configuration:
```shell
python3 run.py --test-notifications
```
This will send a test message to all chat IDs listed in the **tg_chats_to_notify** section of the configuration file. You will see a full Telegram API error text if something won't succeed. In case of failure, the full Telegram API error text will be shown, allowing you to debug easily.
##### 6. Run the script once manually to check all sites immediately:
```shell
python3 run.py --force
```
This will check all sites listed in the configuration file regardless of their schedule.
##### 7. Add the script to your crontab to run it every minute:
```shell
crontab -e
```
Add the following line:
```shell
* * * * * python3 /path/to/self-hosted-tg-alert-sites-monitoring-tool/run.py
```

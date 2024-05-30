## Self-hosted sites monitoring tool with Telegram alerts on errors
This is a self-hosted site monitoring tool that checks the availability of websites using GET, POST, and HEAD requests. The tool looks for a specified text on the monitored page, as defined in the configuration. It sends notifications to specified Telegram accounts (or channels/chats) and allows you to flexibly schedule monitoring tasks using a cron-like schedule.

### Features
- Supports GET, POST, and HEAD requests for monitoring website availability
- Searches for specified text on the monitored page to ensure content validity
- Sends notifications to Telegram on errors
- Flexible scheduling with cron-like syntax
- Customizable through a YAML configuration file
- Offers debug modes to effortlessly identify required Telegram chat IDs, debug Telegram API token configuration and test everything without hassle

### Installation
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

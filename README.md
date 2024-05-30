## Self-Hosted sites monitoring tool with Telegram alerts on errors
This is a self-hosted site monitoring tool that checks the availability of websites using GET, POST, and HEAD requests. The tool looks for a specified text on the monitored page, as defined in the configuration. It sends notifications to specified Telegram accounts (or channels/chats) and allows you to flexibly schedule monitoring tasks using a cron-like schedule.

### Features
- Supports GET, POST, and HEAD requests for monitoring website availability
- Searches for specified text on the monitored page to ensure content validity
- Sends notifications to Telegram on errors
- Flexible scheduling with cron-like syntax
- Customizable through a YAML configuration file
- Offers debug modes to effortlessly identify required Telegram chat IDs, debug Telegram API token configuration and test everything without hassle

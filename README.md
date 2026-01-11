A Python script that reminds me what bin collection week it is, using a Discord webhook.
Designed to run on my Raspberry Pi

# Usage
* Install the python dependencies
* Copy .env.example and rename it .env
* Add your Discord webhook URL `WEBHOOK_URL` and postcode `RECYCLING_POSTCODE` to .env
* Add the Python script to your crontab to run at 6pm the day before collection. For example, to run on Tuesday:
```
0 18 * * 2 /home/username/binremind/venv/bin/python /home/username/binremind/script.py
```
It will send a message to the Discord webhook specified in .env every week.

# Options
* `PING_USER_IDS` - Comma-separated list of Discord user IDs to ping.
* `RANDOMIZE_PING` - Pick one user at random to pick (it's their turn to take it out!)
* `HOLIDAY_RANGE_START` and `HOLIDAY_RANGE_END` - Approximate range in which the holiday collection dates apply (these are posted on social media, not the council website, so it's a lot trickier to automate). Any collections within these dates will link to the social media.

Confirmed working as of 11th January 2026. The script scrapes the council website, so it may break unexpectedly in future.

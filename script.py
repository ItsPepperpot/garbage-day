import sys
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import os

def send_webhook(webhook_url, data):
    # Trigger Discord webhook
    response = requests.post(webhook_url, json=data)

    print(response.status_code)
    print(response.text)

def is_in_holiday_range(start_date_str, end_date_str):
    today = datetime.now()
    year = today.year

    start_date = datetime.strptime(f"{start_date_str}-{year}", "%d-%m-%Y")
    end_date = datetime.strptime(f"{end_date_str}-{year}", "%d-%m-%Y")

    # If the end date is before the start date, it means the range spans into the next year
    if end_date < start_date:
        end_date = end_date.replace(year=year + 1)

    print(f"Holiday range: {start_date} to {end_date}, today: {today}")
    return start_date <= today <= end_date

def main():
    load_dotenv()
    webhook_url = os.getenv("WEBHOOK_URL")
    page_url = os.getenv("RECYCLING_PAGE_URL")
    ping_user_ids = os.getenv("PING_USER_IDS")
    holiday_range_start = os.getenv("HOLIDAY_RANGE_START")
    holiday_range_end = os.getenv("HOLIDAY_RANGE_END")

    if (not webhook_url) or (not page_url):
        print("Error: WEBHOOK_URL and RECYCLING_PAGE_URL must be set in .env")
        sys.exit(1)

    # Parse start/end dates as DD-MM and check if today is in that range
    in_holiday_range = is_in_holiday_range(holiday_range_start, holiday_range_end)

    ping_user_ids = ping_user_ids.split(",") if ping_user_ids else []

    session = requests.Session()

    # Webhook message content
    # TODO get from webpage
    color = "pink"

    # Embed content
    bins_text = {
        "green": "\n * 🟢 Green bags (📦 paper/card, and 🍾 glass/metal)\n * 🗑️ General waste\n * 🍉 Food waste bin",
        "pink": "\n * 🧴 Pink plastic bag\n * 🍉 Food waste bin\n * 🌿 Garden waste bag"
    }

    embed_colors = {
        "green": 2263842,  # forestgreen
        "pink": 13047173  # mediumvioletred
    }

    # Ping specific users
    ping_text = " ".join([f"<@{user_id}>" for user_id in ping_user_ids])
    embed_description = f"♻️ It's {color} bin week! Remember to put out the **{bins_text[color]}** for collection."

    # Add holiday note if in holiday range
    if (in_holiday_range):
        embed_description += ("\n\n🎄 **Note:** Collection dates may differ during the "
        "holiday period—make sure to check updates on "
        "[Facebook](https://www.facebook.com/SwanseaRecycles) or "
        "[X](https://x.com/Recycle4Swansea)."
        )

    data = {
        "content": f"It's {color} bin week! {ping_text}",
        "username": "Bin Reminder",
        "embeds": [
            {
                "title": "Bin Collection Reminder",
                "description": embed_description,
                "color": embed_colors[color],
                "thumbnail": {
                    "url": "https://i.postimg.cc/fTbChSw-9/image.png"
                }
            }
        ]
    }

    send_webhook(webhook_url, data)

if __name__ == "__main__":
    main()

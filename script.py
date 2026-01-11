import sys
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import random
import os

verbose = False
webhook_url = ""

def v_print(string):
    if verbose:
        print(string)

def send_webhook(webhook_url, data):
    # Trigger Discord webhook
    response = requests.post(webhook_url, json=data)

    # Log response
    v_print(f"Discord Reponse:\n  code: {response.status_code}")
    v_print(f"  text: {response.text}")

def get_error_message(text):
    return {
        "content": "Oh no... an error occurred in the Bin Reminder script 🥺",
        "username": "Bin Reminder",
        "embeds": [
            {
                "title": "Error",
                "description": text,
                "color": 16711680  # red
            }
        ]
    }

def is_in_holiday_range(collection_date, start_date_str, end_date_str):
    year = collection_date.year

    start_date = datetime.strptime(f"{start_date_str}-{year}", "%d-%m-%Y")
    end_date = datetime.strptime(f"{end_date_str}-{year}", "%d-%m-%Y")

    # If the end date is before the start date, it means the range spans into the next year
    if end_date < start_date:
        end_date = end_date.replace(year=year + 1)

    v_print(f"Holiday range: {start_date} to {end_date}, collection date: {collection_date}")
    return start_date <= collection_date <= end_date

def scrape_color_from_page(page_url, postcode, save_response=False):
    session = requests.Session()
    resp = session.get(page_url)
    soup = BeautifulSoup(resp.text, "html.parser")

    def get(name):
        el = soup.find("input", {"name": name})
        return el["value"] if el else ""

    payload = {
        "__VIEWSTATE": get("__VIEWSTATE"),
        "__EVENTVALIDATION": get("__EVENTVALIDATION"),
        "__VIEWSTATEGENERATOR": get("__VIEWSTATEGENERATOR"),
        "__VIEWSTATEENCRYPTED": "",

        "txtRoadName": "",
        "txtPostCode": postcode,
        "btnSearch": "Search"
    }

    resp = session.post(
        page_url,
        data=payload,
        headers={
            "Referer": page_url,
            "User-Agent": "Mozilla/5.0"
        }
    )

    # Save response to file for debugging
    if save_response:
        with open("search_results.html", "w", encoding="utf-8") as f:
            f.write(resp.text)

    # Find elements with ids lblNextRefuse (green week) and lblNextRecycling (pink week)
    # Parse element contents to get the next greek and pink week dates respectively
    soup = BeautifulSoup(resp.text, "html.parser")

    # Dates are in format dd/mm/yyyy
    green_week_elem = soup.find(id="lblNextRecycling")
    pink_week_elem = soup.find(id="lblNextRefuse")

    if not green_week_elem or not pink_week_elem:
        error = "Error: Could not find bin week elements on page."
        print(error)
        send_webhook(webhook_url, get_error_message(error))
        sys.exit(1)

    green_week_text = green_week_elem.get_text(strip=True)
    pink_week_text = pink_week_elem.get_text(strip=True)

    v_print(f"Green week text: {green_week_text}")
    v_print(f"Pink week text: {pink_week_text}")

    green_date = datetime.strptime(green_week_text, "%d/%m/%Y")
    pink_date = datetime.strptime(pink_week_text, "%d/%m/%Y")
    today = datetime.today()

    # Determine which week is next based on the dates
    if green_date >= today and (green_date <= pink_date or pink_date < today):
        return "green", green_date
    elif pink_date >= today:
        return "pink", pink_date
    else:
        return None

def get_webhook_body(color, collection_date, ping_user_ids, in_holiday_range, randomize_ping):
     # Embed content
    bins_text = {
        "green": "\n * 🟢 Green bags (📦 paper/card, and 🍾 glass/metal)\n * 🗑️ General waste\n * 🍉 Food waste bin",
        "pink": "\n * 🧴 Pink plastic bag\n * 🍉 Food waste bin\n * 🌿 Garden waste bag"
    }

    embed_colors = {
        "green": 2263842,  # forestgreen
        "pink": 13047173  # mediumvioletred
    }

    # Ping users, or one at random
    v_print(f"User IDs to ping: {ping_user_ids}, randomize: {randomize_ping}")
    if randomize_ping:
        if ping_user_ids:
            # Shuffle
            random.shuffle(ping_user_ids)
            ping_user_ids = [random.choice(ping_user_ids)]
        else:
            ping_user_ids = []

    ping_text = " ".join([f"<@{user_id}>" for user_id in ping_user_ids])
    embed_description = f"♻️ It's {color} bin week! Remember to put out the **{bins_text[color]}** for collection."

    # Add holiday note if in holiday range
    if (in_holiday_range):
        embed_description += ("\n\n🎄 **Note:** Collection dates may differ during the "
        "holiday period—make sure to check updates on "
        "[Facebook](https://www.facebook.com/SwanseaRecycles) or "
        "[X](https://x.com/Recycle4Swansea)."
        )

    return {
        "content": f"It's {color} bin week! {ping_text} ({collection_date.strftime('%d/%m/%Y')})",
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

def main():
    v_print(f"Starting bin reminder script at {datetime.now()}...")

    v_print("Loading environment variables...")

    load_dotenv()
    global webhook_url
    webhook_url = os.getenv("WEBHOOK_URL")
    page_url = os.getenv("RECYCLING_PAGE_URL")
    ping_user_ids = os.getenv("PING_USER_IDS")
    ping_user_ids = ping_user_ids.split(",") if ping_user_ids else []

    holiday_range_start = os.getenv("HOLIDAY_RANGE_START")
    holiday_range_end = os.getenv("HOLIDAY_RANGE_END")
    postcode = os.getenv("RECYCLING_POSTCODE")
    randomize_ping = os.getenv("RANDOMIZE_PING", "false").lower() == "true"

    if (not webhook_url) or (not page_url):
        print("Error: WEBHOOK_URL and RECYCLING_PAGE_URL must be set in .env")
        sys.exit(1)

    v_print("Fetching recycling week from council page...")
    result = scrape_color_from_page(page_url, postcode)

    if not result:
        error = "Error: Could not determine bin color for this week."
        print(error)
        send_webhook(webhook_url, get_error_message(error))
        sys.exit(1)

    color, collection_date = result

    v_print("Checking if collection date is in holiday range...")
    in_holiday_range = is_in_holiday_range(collection_date, holiday_range_start, holiday_range_end)

    data = get_webhook_body(color, collection_date, ping_user_ids, in_holiday_range, randomize_ping)

    v_print("Sending webhook...")
    send_webhook(webhook_url, data)
    v_print("Done!")

if __name__ == "__main__":
    main()

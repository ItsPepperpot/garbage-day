from dotenv import load_dotenv
import requests
import os

load_dotenv()
webhook_url = os.getenv("WEBHOOK_KEY")
api_url = os.getenv("API_URL")

# Webhook message content
data = {
    "content": "",
    "username": "Bin Reminder"
}

# Trigger Discord webhook
response = requests.post(webhook_url, data=data)

print(response.status_code)
print(response.text)

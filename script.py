import requests

url = ""

data = {
    "content": "hello from raspberry pi :3",
    "username": "Bin Reminder"
}

response = requests.post(url, data=data)

print(response.status_code)
print(response.text)

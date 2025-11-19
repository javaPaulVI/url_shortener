import requests

# URL of your FastAPI endpoint
API_URL = "https://opulent-succotash-97xx77j9xwq37w7-8000.app.github.dev/api/shorten"  # change if your server runs elsewhere

# The long URL you want to shorten
payload = {
    "long_url": "https://pornhub.com",  # replace with the website you want to register
    "alias": "ph"  # optional; must be unique
}

try:
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()  # raises an error for 4xx/5xx status codes
except requests.exceptions.RequestException as e:
    print("Error:", e)
else:
    try:
        data = response.json()
        print("URL registered successfully!")
        print("Short URL:", data.get("short_url"))
        print("Original URL:", data.get("long_url"))
        print("Alias:", data.get("alias"))
    except ValueError:
        print("Server did not return JSON:", response.text)

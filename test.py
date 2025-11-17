import requests

url = "http://127.0.0.1:8000/api/get_stats/google"  # your POST endpoint

data = {
    "long_url": "https://google.com",
    "alias": "google"  # optional
}

response = requests.get(url)
print(response.status_code)
print(response.json())

import requests
import json

latitude = 42.279594
longitude = -83.732124
url = f"https://api.weather.gov/points/{latitude},{longitude}"

data_dict = requests.get(url)
print(data_dict.json())
print(data_dict.json()["properties"])
import requests

latitude = 0
longitude = 0
url = f"https://api.weather.gov/points/{latitude},{longitude}"

data_dict = requests.get(url)
print(data_dict)
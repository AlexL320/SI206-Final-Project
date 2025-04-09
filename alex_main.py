import requests

lat = 1
lon = 1
API_key = ""

url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={API_key}"

data_dict = requests.get(url)
print(data_dict)


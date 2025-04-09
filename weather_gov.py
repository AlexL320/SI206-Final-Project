import requests
import json

latitude = 42.279594
longitude = -83.732124
url_one = f"https://api.weather.gov/points/{latitude},{longitude}"

api_dict = requests.get(url_one)
#print(data_dict.json())
#print(api_dict.json()["properties"]["forecast"])

url_daily = api_dict.json()["properties"]["forecast"]
forecast_dict = requests.get(url_daily)

#Daily Forcast for the next 14 days
#print(forecast_dict.json()["properties"]["periods"])
data_list = forecast_dict.json()["properties"]["periods"]
""" for day in data_list:
    print(day) """
    
#Hourly Forcast for the next 14 days
url_hourly = api_dict.json()["properties"]["forecastHourly"]
forecast_dict = requests.get(url_hourly)
print(forecast_dict.json())
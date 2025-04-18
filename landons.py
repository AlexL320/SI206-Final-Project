import requests
import csv
from datetime import datetime

api_key = 'N9DKDVJTSMT2WMRKEJBM7ZQ83'

games = [
   ('2023-09-08', 'Kansas City'),
   ('2023-09-10', 'Baltimore'),
   ('2023-09-10', 'Seattle'),
   ('2023-09-11', 'East Rutherford'),
   ('2023-09-12', 'East Rutherford'),
   ('2023-09-15', 'Philadelphia'),
   ('2023-09-17', 'Houston'),
   ('2023-09-17', 'Glendale'),
   ('2023-09-17', 'Denver'),
   ('2023-09-18', 'Foxborough'),
   ('2023-09-18', 'Charlotte'),
   ('2023-09-19', 'Pittsburgh'),
   ('2023-09-22', 'Santa Clara'),
   ('2023-09-24', 'Baltimore'),
   ('2023-09-24', 'Seattle'),
   ('2023-09-24', 'Glendale'),
   ('2023-09-25', 'Las Vegas'),
   ('2023-09-25', 'Tampa'),
   ('2023-09-26', 'Cincinnati'),
   ('2023-09-29', 'Green Bay'),
   ('2023-10-01', 'London'),
   ('2023-10-01', 'Houston'),
   ('2023-10-01', 'Inglewood'),
   ('2023-10-01', 'Santa Clara'),
   ('2023-10-02', 'East Rutherford'),
   ('2023-10-03', 'East Rutherford'),
   ('2023-10-06', 'Landover'),
   ('2023-10-08', 'London'),
   ('2023-10-08', 'Pittsburgh'),
   ('2023-10-08', 'Glendale'),
   ('2023-10-08', 'Minneapolis'),
   ('2023-10-09', 'Santa Clara'),
   ('2023-10-10', 'Las Vegas'),
   ('2023-10-13', 'Kansas City'),
   ('2023-10-15', 'London'),
   ('2023-10-15', 'Houston'),
   ('2023-10-15', 'Las Vegas'),
   ('2023-10-15', 'Tampa'),
   ('2023-10-16', 'Orchard Park'),
   ('2023-10-17', 'Inglewood'),
   ('2023-10-20', 'New Orleans'),
   ('2023-10-22', 'Baltimore'),
   ('2023-10-22', 'Seattle'),
   ('2023-10-22', 'Kansas City'),
   ('2023-10-23', 'Philadelphia'),
   ('2023-10-24', 'Minneapolis'),
   ('2023-10-27', 'Orchard Park'),
   ('2023-10-29', 'Charlotte'),
   ('2023-10-29', 'Seattle'),
   ('2023-10-29', 'Santa Clara'),
   ('2023-10-30', 'Inglewood'),
   ('2023-10-31', 'Detroit'),
   ('2023-11-03', 'Pittsburgh'),
   ('2023-11-05', 'Frankfurt'),
   ('2023-11-05', 'Houston'),
   ('2023-11-05', 'Charlotte'),
   ('2023-11-05', 'Philadelphia'),
   ('2023-11-06', 'Cincinnati'),
   ('2023-11-07', 'East Rutherford'),
   ('2023-11-10', 'Chicago'),
   ('2023-11-12', 'Frankfurt'),
   ('2023-11-12', 'Baltimore'),
   ('2023-11-12', 'Inglewood'),
   ('2023-11-12', 'Seattle'),
   ('2023-11-13', 'Las Vegas'),
   ('2023-11-14', 'Orchard Park'),
   ('2023-11-17', 'Baltimore'),
   ('2023-11-19', 'Houston'),
   ('2023-11-19', 'Santa Clara'),
   ('2023-11-19', 'Inglewood'),
   ('2023-11-20', 'Denver'),
   ('2023-11-21', 'Kansas City'),
   ('2023-11-23', 'Detroit'),
   ('2023-11-23', 'Arlington'),
   ('2023-11-24', 'Seattle'),
   ('2023-11-24', 'East Rutherford'),
   ('2023-11-26', 'Houston'),
   ('2023-11-26', 'Glendale'),
   ('2023-11-26', 'Philadelphia'),
   ('2023-11-27', 'Inglewood'),
   ('2023-11-28', 'Minneapolis'),
   ('2023-12-01', 'Arlington'),
   ('2023-12-03', 'Houston'),
   ('2023-12-03', 'Tampa'),
   ('2023-12-03', 'Philadelphia'),
   ('2023-12-04', 'Green Bay'),
   ('2023-12-05', 'Jacksonville'),
   ('2023-12-08', 'Pittsburgh'),
   ('2023-12-10', 'Baltimore'),
   ('2023-12-10', 'Santa Clara'),
   ('2023-12-10', 'Inglewood'),
   ('2023-12-11', 'Arlington'),
   ('2023-12-12', 'East Rutherford'),
   ('2023-12-15', 'Las Vegas'),
   ('2023-12-16', 'Cincinnati'),
   ('2023-12-16', 'Indianapolis'),
   ('2023-12-17', 'Detroit'),
   ('2023-12-17', 'Charlotte'),
   ('2023-12-17', 'Glendale'),
   ('2023-12-17', 'Orchard Park')
]

weather_elements = "datetime,tempmax,tempmin,humidity,precip,preciptype,windspeedmax,windspeedmin,uvindex,description"

with open('nfl_weather_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Game Date', 'Location', 'Max Temperature (F)', 'Min Temperature (F)', 'Precipitation (inches)', 'Wind Speed (mph)', 'Humidity (%)', 'UV Index', 'Conditions'])

    for game in games:
        game_date, location = game
        formatted_date = datetime.strptime(game_date, '%Y-%m-%d').date()
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{formatted_date}/{formatted_date}?unitGroup=us&elements={weather_elements}&key={api_key}&contentType=csv&include=days"
        response = requests.get(url)

        if response.status_code == 200:
            print(f"Success: Data for {location} on {formatted_date} fetched successfully.")
            csv_data = response.text.splitlines()
            for row in csv_data[1:]:
                data = row.split(',')
                writer.writerow([formatted_date, location] + data[1:])  
        else:
            print(f"Error fetching data for {location} on {formatted_date}: {response.status_code}")
            print(f"Error response text: {response.text}")
print("Weather data for NFL games has been saved to nfl_weather_data.csv.")

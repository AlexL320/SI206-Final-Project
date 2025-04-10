import requests
url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Ann%20Arbor/2024-12-01/2025-04-09?unitGroup=us&elements=datetime%2Cname%2Ctempmax%2Ctempmin%2Chumidity%2Cprecip%2Cpreciptype%2Cwindspeedmax%2Cwindspeedmin%2Cuvindex%2Cconditions&include=days&key=N9DKDVJTSMT2WMRKEJBM7ZQ83&contentType=csv'
response = requests.get(url)
if response.status_code == 200:
    with open('ann_arbor_weather_data.csv', 'wb') as file:
        file.write(response.content)
else:
    print(f"Error: {response.status_code}")
    print(response.text)

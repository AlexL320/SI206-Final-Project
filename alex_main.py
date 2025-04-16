import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population"

response = requests.get(url)
if response.status_code == 200:
        html = response.text
else:
    print("Fail to retrieve the web page.")
soup = BeautifulSoup(html,'html.parser')

cord = []
table = soup.find('table', class_='sortable wikitable sticky-header-multi static-row-numbers sort-under col1left col2center')
table_body = table.find('tbody')
cities_data = table_body.find_all('tr')
for city_info in cities_data:
    box = city_info.find_all('td')
    city = None
    state = None
    if len(box) != 0:
        city = box[0].getText().strip()
        state = box[1].getText().strip()
    mytuple = (city, state)
    print(mytuple)
    coordinates = city_info.find_all('span', class_ = 'geo')
    if len(coordinates) != 0:
        print(coordinates[0].getText())

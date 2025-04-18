import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import os

#Creates the database
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + "locations.db")
cur = conn.cursor()

#Url to the wikipedia page
url = "https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population"

response = requests.get(url)
if response.status_code == 200:
        html = response.text
else:
    print("Fail to retrieve the web page.")
soup = BeautifulSoup(html,'html.parser')

#Gets the data
tuple_lst = []
table = soup.find('table', class_='sortable wikitable sticky-header-multi static-row-numbers sort-under col1left col2center')
table_body = table.find('tbody')
cities_data = table_body.find_all('tr')
state_lst = []
for city_info in cities_data:
    box = city_info.find_all('td')
    city = None
    state = None
    #popuatlion = None
    if len(box) != 0:
        city = box[0].getText().strip()
        pattern = r'\[+\w+\]'
        city_line = re.findall(pattern, city)
        #print(city)
        if city_line:
            city = city[:-3]
        state_pos = box[1].getText().strip()
        if state_pos not in state_lst:
            state_lst.append(state_pos)
        position = state_lst.index(state_pos)
        state = position
    coordinates = city_info.find_all('span', class_ = 'geo')
    if len(coordinates) != 0:
        #print(coordinates[0].getText())
        cor = coordinates[0].getText().split(';')
        latitude = cor[0].strip()
        longitude = cor[1].strip()
        #Create the tuple
        loct_tup = (city, state, latitude, longitude)
        #print(loct_tup)
        tuple_lst.append(loct_tup)
#print(tuple_lst)

#Database
cur.execute(""" CREATE TABLE IF NOT EXISTS locations (city STRING, state INTEGER, longitude INTEGER, latitude INTEGER, UNIQUE(city, state, longitude, latitude)) """)
conn.commit()
count = 0
for tup in tuple_lst:
    if count == 25:
        print("Done with inputing data")
        break
    else:
        city = tup[0]
        state = tup[1]
        longitude = tup[2]
        latitude = tup[3]
        #population = tup[4]
        if cur.execute("SELECT * FROM locations WHERE city=? AND state=? AND longitude=? AND latitude=?", (city, state, longitude, latitude)).fetchall():
            continue
        else:
            cur.execute("INSERT OR IGNORE INTO locations (city, state, longitude, latitude) VALUES (?,?,?,?)", (city, state, longitude, latitude))
            conn.commit()
            count += 1
            print("inputing data")

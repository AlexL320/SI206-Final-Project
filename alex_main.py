import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import os
import matplotlib.pyplot as plt
from dennis import average_dict

import_dict = average_dict
#print("Imported list")
#print(import_dict)


#Creates the database
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + "locations.db")
cur = conn.cursor()

#Url to the wikipedia page
url = "https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population"
#goes to the website
response = requests.get(url)
if response.status_code == 200:
        html = response.text
else:
    print("Fail to retrieve the web page.")
soup = BeautifulSoup(html,'html.parser')


#Gets the data
tuple_lst = []
#finds the table
table = soup.find('table', class_='sortable wikitable sticky-header-multi static-row-numbers sort-under col1left col2center')
table_body = table.find('tbody')
cities_data = table_body.find_all('tr')
state_lst = []
#goes through the body to find the city's name and state
def get_data():
    for city_info in cities_data:
        box = city_info.find_all('td')
        city = None
        state = None
        population = None
        #gets the city data if the row is not empty
        if len(box) != 0:
            #city data
            city = box[0].getText().strip()
            pattern = r'\[+\w+\]'
            city_line = re.findall(pattern, city)
            #print(city)
            if city_line:
                city = city[:-3]
            state = box[1].getText().strip()
            if state not in state_lst:
                state_lst.append(state)
            population = box[2].getText().strip()

        #find the latitude and longitude of the city
        coordinates = city_info.find_all('span', class_ = 'geo')
        if len(coordinates) != 0:
            #print(coordinates[0].getText())
            cor = coordinates[0].getText().split(';')
            latitude = cor[0].strip()
            longitude = cor[1].strip()
            #Create the tuple
            loct_tup = (city, state, latitude, longitude, population)
            #print(loct_tup)
            tuple_lst.append(loct_tup)
    #print(tuple_lst)
    return tuple_lst

def create_location_database():
    #Database
    #creates the database
    cur.execute(""" CREATE TABLE IF NOT EXISTS locations (city STRING, state INTEGER, longitude INTEGER, latitude INTEGER, population INTEGER, UNIQUE(city, state, longitude, latitude, population)) """)
    conn.commit()
    count = 0
    #puts in 25 rows of data into the data base
    for tup in tuple_lst:
        #stops after 25 rows of data are put into the data base
        if count == 25:
            print("Done with inputing data")
            break
        else:
            city = tup[0]
            state = tup[1]
            state = state_lst.index(state)
            longitude = tup[2]
            latitude = tup[3]
            population = tup[4]
            #population = tup[4]
            #adds the rows already in the database when running the code
            if cur.execute("SELECT * FROM locations WHERE city=? AND state=? AND longitude=? AND latitude=? AND population=?", (city, state, longitude, latitude, population)).fetchall():
                continue
            #adds new rows of data into the database
            else:
                cur.execute("INSERT OR IGNORE INTO locations (city, state, longitude, latitude, population) VALUES (?,?,?,?,?)", (city, state, longitude, latitude, population))
                conn.commit()
                count += 1
                print("inputing data")

def create_scatter_graph():
    #visualization
    graph_x = []
    graph_y = []
    labels = []
    for tup in tuple_lst:
        temp_tup = (tup[0], tup[1])
        for k, v in import_dict.items():
            if k == temp_tup:
                graph_x = [v] + graph_x
                graph_y = [tup[4]] + graph_y
                labels = [temp_tup] + labels
    for i, label in enumerate(labels):
        plt.annotate(label, (graph_x[i], graph_y[i]), textcoords="offset points", xytext=(0,5), ha='center')
    plt.xlabel("percentage")
    plt.ylabel("population")
    plt.scatter(graph_x, graph_y)
    plt.show()

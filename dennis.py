import requests
import json
import sqlite3
import os
from datetime import datetime
import math
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import numpy as np 


# Creates the databse
path = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(path + "/" + "NFL_game.db")
cur = conn.cursor()

# Gets the API data for every NFL games in the eyar 2023
monday_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=2023"
monday_dict = requests.get(monday_url)
monday_data = monday_dict.json()
monday_att = monday_data["events"]
city_list = []
data_dict = {}
count = 0
for day in monday_att:
    season_type = day["season"]['slug']
    #print(day["season"])
    date_month = day["date"][5:7]
    
    # Checks if the game is in the 2023-2024 regular season
    if season_type == 'regular-season' and int(date_month) > 8:
        #print(day["date"])
        for game in day["competitions"]:
            #print(game["id"])
            #print("__________________________________")
            #print(game["attendance"])
            #print(game["venue"]["address"]["city"])
            if "state" in game["venue"]["address"].keys():
                loc_tuple = (game["venue"]["address"]["city"], game["venue"]["address"]["state"])
            else:
                loc_tuple = (game["venue"]["address"]["city"], game["venue"]["address"]["country"])
            #print(loc_tuple)
            data_dict[day["date"]] = [loc_tuple, game['attendance']]
            if loc_tuple not in city_list:
                city_list.append(loc_tuple)
        #print(count)
#print(city_list)
#print(data_dict)


# Pulls the data from the page of the max capacity of all NFL game stadiums
wiki_url = "https://en.wikipedia.org/wiki/List_of_current_NFL_stadiums"
request = requests.get(wiki_url)

if request.status_code == 200:
    html = request.text
else:
    print("Failed to retrieve the web page.")
    
soup = BeautifulSoup(html,'html.parser')

# Finds the data within the wiki page
table = soup.find('table', class_='wikitable sortable plainrowheaders')
#print(table)

# Gets the data of the staiums into a list
table_body = table.find('tbody')
stadiums = table_body.find_all('tr')
stadium_dict = {}

for stadium in stadiums:
    capacity = stadium.find_all('td')
    if len(capacity) >= 7:
        #print(capacity[2].getText(), capacity[3].getText())
        #print(capacity[2].getText().strip("\n").split(","))
        city_name = capacity[2].getText().strip("\n").split(",")[0]
        max_captacity = int(capacity[3].getText().strip("\n").replace(",", ""))
        #print(city_name)
        for city in city_list:
            if city_name == city[0]:
                stadium_dict[city_name] = max_captacity
#print(stadium_dict)
#print(city_list)


# Creates the database for the city list
cur.execute(""" CREATE TABLE IF NOT EXISTS Location (number INTEGER, location Text, UNIQUE (number, location)) """)
conn.commit()

# Creates the databsse and adds the header
cur.execute(""" CREATE TABLE IF NOT EXISTS Games (year INTEGER, month INTEGER, day INTEGER, location INTEGER, attendance INTEGER, capacity INTEGER, UNIQUE (year, month, day, location, attendance, capacity)) """)
conn.commit()


attendance_list = []
data_counter = 0
index_counter = 0
maximum = 0
for key,value in data_dict.items():
    #print(key, value)
    if data_counter == 25:
        break
    else:
        year = key[0:4]
        month = key[5:7]
        day = key[8:10]
        for index in range(0, len(city_list)):
            if str(city_list[index]) == str(value[0]):
                #print(str(city_list[index]))
                #print(str(value[0]))
                for k,y in stadium_dict.items():
                    if str(k) == str(city_list[index][0]):
                        maximum = y
                location = index
        attendance = value[1]
        attendance_list.append(attendance)
        if cur.execute("SELECT * FROM Games WHERE year=? AND month=? AND day=? AND location=? AND attendance=? AND capacity=?", (year, month, day, location, attendance, maximum)).fetchall():
            continue
        else:
            cur.execute("INSERT OR IGNORE INTO Games (year, month, day, location, attendance, capacity) VALUES (?,?,?,?,?,?)", (year, month, day, location, attendance, maximum))
            cur.execute("INSERT OR IGNORE INTO Location (number, location) VALUES (?,?)", (location, str(city_list[location])))
            conn.commit()
            data_counter += 1

startDate = datetime.strptime('8/18/2008', "%m/%d/%Y")
endDate = datetime.strptime('9/26/2008', "%m/%d/%Y")

""" delta = endDate - startDate
#print(delta.days) 
day_list = []
for i in range(1, math.ceil(delta.days) + 1):
    day_list.append(f"Day {i}") """
    
#print(day_list)
#print(len(day_list))
#print(len(attendance_list))


# Creates the dicitonaries that will be used for the bar graph
game_attendance_dict = {}
average_dict= {}
game_key = ""
for key,values in stadium_dict.items():
    #print(key)
    percent_list = []
    day_counter = 0
    total_percent = 0.0
    for index,items in data_dict.items():
        #print(items[0][0])
        #print(index)
        if key == items[0][0]:
            game_key = items[0]
            #print("match")
            #print(items[1])
            #print(values)
            percentage = items[1] / values
            percentage = int(percentage * 10000) / 10000
            day_percent = (index, percentage)
            percent_list.append(day_percent)
            #print(percent_list)
            day_counter += 1
            total_percent += percentage
    game_attendance_dict[game_key] = percent_list
    if day_counter > 0:
        average_dict[game_key] = round(((int((total_percent / int(day_counter)) * 10000) / 10000) * 100), 2)

#print(game_attendance_dict)
#print(average_dict)

# Creates the list that will be used to label to graph
graph_x = []
graph_y = []
for key, value in average_dict.items():
    graph_x.append(str(key[0] + ", " + key[1]))
    graph_y.append(float(value))
print(graph_x)
print(graph_y)

# Plots the attendance as a bar graph
plt.barh(graph_x, graph_y)
plt.title("Average attendance percentage for each NFL stadium")
plt.xlabel("Stadium City Location")
plt.ylabel("Percentage")

# Adds the percentage to the end of each bar in the bar graph
for index in range(len(graph_x)):
    plt.text(graph_y[index], graph_x[index], str(graph_y[index]), va="center")

plt.show()
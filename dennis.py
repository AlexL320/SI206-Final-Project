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
# The URL from the API github
monday_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=2023"
monday_dict = requests.get(monday_url)
monday_data = monday_dict.json()

# Get ths data from the main dictionary
monday_att = monday_data["events"]

# Creates a city_list to be used to assign each city an index in the "location" table in the NFL_game database
city_list = []
# Creates a data_dict to store the time, location index, and attendance of each NFl game in the "game" table in the NFL_game database
data_dict = {}

# Loops throught each game in the API dictionary
for day in monday_att:
    # Gets which part of the NFL season the game was played in.
    season_type = day["season"]['slug']
    #print(day["season"])
    # Gets the month of the game
    date_month = day["date"][5:7]
    
    # Checks if the game is in the 2023-2024 regular season
    if season_type == 'regular-season' and int(date_month) > 8:
        #print(day["date"])
        # Loops throught the details of every game to find the location and attendance
        for game in day["competitions"]:
            #print(game["id"])
            #print("__________________________________")
            #print(game["attendance"])
            #print(game["venue"]["address"]["city"])
            # Checks if the city is in the United States and gets the location if it does
            if "state" in game["venue"]["address"].keys():
                loc_tuple = (game["venue"]["address"]["city"], game["venue"]["address"]["state"])
            # Continues if the location is not within the states
            else:
                continue
                #loc_tuple = (game["venue"]["address"]["city"], game["venue"]["address"]["country"])
            #print(loc_tuple)
            # Adds the location and attendance number to data_dict
            data_dict[day["date"]] = [loc_tuple, game['attendance']]
            # Adds the location to city_list. Does skip over duplicates
            if loc_tuple not in city_list:
                city_list.append(loc_tuple)
#print(data_dict)


# Pulls the data from the page of the max capacity of all NFL game stadiums
wiki_url = "https://en.wikipedia.org/wiki/List_of_current_NFL_stadiums"
request = requests.get(wiki_url)

# Checks if accessing the wiki link is successful and prints an error message if it was not.
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

# Creates a dictionary to store the max capacity to each corresponding stadium
stadium_dict = {}

# Loops throught all the "tr" elements
for stadium in stadiums:
    # Find the "td" elements in each "tr" elements to get the specifications
    capacity = stadium.find_all('td')
    # Checks if the "td" element is large enought to contain all of data
    if len(capacity) >= 7:
        #print(capacity[2].getText(), capacity[3].getText())
        #print(capacity[2].getText().strip("\n").split(","))
        
        # Creates two variables to store the city name and the max capacity of each NFL stadium
        city_name = capacity[2].getText().strip("\n").split(",")[0]
        max_captacity = int(capacity[3].getText().strip("\n").replace(",", ""))
        #print(city_name)
        
        # Loops thorught each NFL game location in city_list
        for city in city_list:
            # Checks if the current city name matches the city name of a game location
            if city_name == city[0]:
                # Stores the max capacity of the stadium to the 
                stadium_dict[city_name] = max_captacity
#print(stadium_dict)
#print(city_list)


# Creates the database for the city list
cur.execute(""" CREATE TABLE IF NOT EXISTS Location (number INTEGER, location Text, UNIQUE (number, location)) """)
conn.commit()

# Creates the databsse and adds the header
cur.execute(""" CREATE TABLE IF NOT EXISTS Games (year INTEGER, month INTEGER, day INTEGER, location INTEGER, attendance INTEGER, capacity INTEGER, UNIQUE (year, month, day, location, attendance, capacity)) """)
conn.commit()

# Creates a attendance list to check if the code is getting the attendance correctly
#attendance_list = []
data_counter = 0
index_counter = 0
maximum = 0

# Loops throught data_dict to begin adding it to the database
for key,value in data_dict.items():
    #print(key, value)
    # Checks if 25 rows of data have been added and breaks if it is true
    if data_counter == 25:
        break
    else:
        # Gets the integers for the year, month, and day of each NFL game in data_dict
        year = key[0:4]
        month = key[5:7]
        day = key[8:10]
        # Loops throught city_list
        for index in range(0, len(city_list)):
            # Checks if the current city name within data_dict matches the current city name within city_list
            if str(city_list[index]) == str(value[0]):
                #print(str(city_list[index]))
                #print(str(value[0]))
                # Loops throught stadium_dict
                for k,y in stadium_dict.items():
                    # Checks if the city name city name match and set the maximum to y
                    if str(k) == str(city_list[index][0]):
                        maximum = y
                # Assigns a location index to the city
                location = index
        # Assigns the attendance of the game to the "attendance" variable
        attendance = value[1]
        #attendance_list.append(attendance)
        # Checks if the row of data already exists within the table of the database.
        if cur.execute("SELECT * FROM Games WHERE year=? AND month=? AND day=? AND location=? AND attendance=? AND capacity=?", (year, month, day, location, attendance, maximum)).fetchall():
            continue
        # Adds the row to the database
        else:
            cur.execute("INSERT OR IGNORE INTO Games (year, month, day, location, attendance, capacity) VALUES (?,?,?,?,?,?)", (year, month, day, location, attendance, maximum))
            cur.execute("INSERT OR IGNORE INTO Location (number, location) VALUES (?,?)", (location, str(city_list[location])))
            conn.commit()
            data_counter += 1

# Creates the dicitonaries that will be used for the bar graph
game_attendance_dict = {}
average_dict= {}
game_key = ""
# Loops throught stadium_dict
for key,values in stadium_dict.items():
    #print(key)
    # Creates a list to store how full each statdium was in each game
    percent_list = []
    # Values that will help determine the average percentage of how full the stadium was in each city
    day_counter = 0
    total_percent = 0.0
    # Loops throught data_dict to find the attendance
    for index,items in data_dict.items():
        #print(items[0][0])
        #print(index)
        # Checks if the city within key in stadium_dict and the city within index in data_dict match
        if key == items[0][0]:
            # Sets the gmae_key to the location of the game within data_dict
            game_key = items[0]
            #print("match")
            #print(items[1])
            #print(values)
            # Calculates how full the stadium was in the current game
            percentage = items[1] / values
            percentage = int(percentage * 10000) / 10000
            day_percent = (index, percentage)
            # Adds the percentage to percent_list
            percent_list.append(day_percent)
            #print(percent_list)
            # Changes the values accordingly
            day_counter += 1
            total_percent += percentage
    # Adds percent_list to the current city
    game_attendance_dict[game_key] = percent_list
    # Calculates how full the each stadium was on average, if there were any games played there
    if day_counter > 0:
        average_dict[game_key] = round(((int((total_percent / int(day_counter)) * 10000) / 10000) * 100), 2)

#print(game_attendance_dict)
#print(average_dict)

# Creates the list that will be used to label to graph
graph_x = []
graph_y = []
# Adds the vakue of how full the each stadium was on average to the end of each bar in the bar graph
for key, value in average_dict.items():
    graph_x.append(str(key[0] + ", " + key[1]))
    graph_y.append(float(value))
print(graph_x)
print(graph_y)

# Plots the attendance as a bar graph
plt.barh(graph_x, graph_y)
# Adds the title and labels to the bar graph
plt.title("Average attendance percentage for each NFL stadium")
plt.xlabel("Stadium City Location")
plt.ylabel("Percentage")

# Adds the percentage to the end of each bar in the bar graph
for index in range(len(graph_x)):
    plt.text(graph_y[index], graph_x[index], str(graph_y[index]), va="center")

plt.show()
import requests
import json
import sqlite3
import os
from datetime import datetime
import math
import matplotlib.pyplot as plt


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

""" for index in range(0, len(city_list)):
    number = index
    location = str(city_list[index])
    cur.execute("INSERT OR IGNORE INTO Location (number, location) VALUES (?,?)", (number, location))
    conn.commit() """

# Creates the database for the city list
cur.execute(""" CREATE TABLE IF NOT EXISTS Location (number INTEGER, location Text, UNIQUE (number, location)) """)
conn.commit()

# Creates the databsse and adds the header
cur.execute(""" CREATE TABLE IF NOT EXISTS Games (year INTEGER, month INTEGER, day INTEGER, location INTEGER, attendance INTEGER, UNIQUE (year, month, day, location, attendance)) """)
conn.commit()


attendance_list = []
data_counter = 0
place = 0
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
                location = index
                place = index
        attendance = value[1]
        attendance_list.append(attendance)
        if cur.execute("SELECT * FROM Games WHERE year=? AND month=? AND day=? AND location=? AND attendance=?", (year, month, day, location, attendance)).fetchall():
            continue
        else:
            cur.execute("INSERT OR IGNORE INTO Games (year, month, day, location, attendance) VALUES (?,?,?,?,?)", (year, month, day, location, attendance))
            cur.execute("INSERT OR IGNORE INTO Location (number, location) VALUES (?,?)", (place, str(city_list[place])))
            conn.commit()
            data_counter += 1

startDate = datetime.strptime('8/18/2008', "%m/%d/%Y")
endDate = datetime.strptime('9/26/2008', "%m/%d/%Y")

delta = endDate - startDate
#print(delta.days) 
day_list = []
for i in range(1, math.ceil(delta.days) + 1):
    day_list.append(f"Day {i}")
print(day_list)
print(len(day_list))
print(len(attendance_list))

fig, ax = plt.subplots()
#ax.plot(day_list, attendance_list, 'b-', label="attendance")
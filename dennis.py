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

# Creates the databse and adds the header
cur.execute(""" CREATE TABLE IF NOT EXISTS Games (date TEXT, location TEXT, attendance INTEGER) """)
conn.commit()


attendance_list = []
for key,value in data_dict.items():
    #print(key, value)
    date = key
    location = str(value[0])
    attendance = value[1]
    attendance_list.append(attendance)
    cur.execute("INSERT OR IGNORE INTO Games (date, location, attendance) VALUES (?,?,?)", (date, location, attendance))
    conn.commit()

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
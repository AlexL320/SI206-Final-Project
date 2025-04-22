import requests
import json
import sqlite3
import os
import math
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import numpy as np 
import re
import csv
from datetime import datetime
import seaborn as sns

def get_game_data():
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
    tuple_data = (data_dict, city_list) 
    return tuple_data

#goes through the body to find the city's name and state
def get_wiki_data():
    #Url to the wikipedia page
    url = "https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population"
    #goes to the website
    response = requests.get(url)
    if response.status_code == 200:
            html = response.text
    else:
        print("Fail to retrieve the web page.")
    soup = BeautifulSoup(html,'html.parser')
    
    #Gets the last city
    end_url = "https://en.wikipedia.org/wiki/East_Rutherford,_New_Jersey"
    end_resp = requests.get(end_url)
    end_html = end_resp.text
    end_soup = BeautifulSoup(end_html,'html.parser')
    
    tuple_lst = []
    #finds the table
    table = soup.find('table', class_='sortable wikitable sticky-header-multi static-row-numbers sort-under col1left col2center')
    table_body = table.find('tbody')
    cities_data = table_body.find_all('tr')
    state_lst = []
    cord_dict = {}
    index = 1
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
            my_tup = (city, state)
            cord_dict[my_tup] = index
            index += 1
            #print(loct_tup)
            tuple_lst.append(loct_tup)
    #print(tuple_lst)
    end_location = None
    end_loca = end_soup.find('span', "mw-page-title-main")
    end_location = end_loca.getText()
    end_loca_lst = end_location.split(',')
    end_city = end_loca_lst[0]
    end_state = end_loca_lst[1][1:2] +end_loca_lst[1][5:6]
    
    end_population = None
    end_table = end_soup.find('table', class_ = "infobox ib-settlement vcard")
    end_pop = end_table.find_all('td', class_ = "infobox-data")
    for end in end_pop:
        if(end.getText() == "10,421"):
            end_population = end.getText()
    
    end_coords = end_soup.find('span', class_ = "geo-dec")
    end_coords_lst= end_coords.getText()
    end_coordinates = end_coords_lst.split(' ')
    end_lat = end_coordinates[0][0:5]
    end_long = end_coordinates[1][0:5]
    end_long = "-" + end_long
    end_tup = (end_city, end_state, end_population, end_lat, end_long)
    tuple_lst.append(end_tup)
    
    #puts the location in the coordinate dictionary
    end_loc_tup = (end_city, end_state)
    cord_dict[end_loc_tup] = index
    
    return [tuple_lst, state_lst, cord_dict]
# Path to the database
def create_db_connection():
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + "Weather.db")
    return conn

# Create the Cities table to store unique cities and their integer IDs
def create_cities_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Cities (
            city_id INTEGER PRIMARY KEY,
            city_name TEXT UNIQUE
        )
    """)
    conn.commit()

# Create the Weather table with city_id column
def create_weather_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Weather (
            game_date TEXT, 
            city_id INTEGER, 
            max_temp REAL, 
            min_temp REAL, 
            precipitation REAL, 
            wind_speed REAL, 
            humidity REAL, 
            uv_index INTEGER, 
            conditions TEXT,
            FOREIGN KEY (city_id) REFERENCES Cities (city_id),
            UNIQUE(game_date, city_id)
        )
    """)
    conn.commit()

# Function to fetch weather data for a specific game and process it
def fetch_weather_data(games, api_key, weather_elements, max_entries):
    conn = create_db_connection()
    create_cities_table(conn)
    create_weather_table(conn)

    city_list = [game[1] for game in games] 
    city_list = list(set(city_list))

    # Insert city data
    cur = conn.cursor()
    for city in city_list:
        cur.execute("INSERT OR IGNORE INTO Cities (city_name) VALUES (?)", (city,))
    conn.commit()

    counter = 0
    with open('nfl_weather_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Game Date', 'Location', 'Max Temperature (F)', 'Min Temperature (F)', 'Precipitation (inches)', 'Wind Speed (mph)', 'Humidity (%)', 'UV Index', 'Conditions'])

        # Loop through the games and fetch weather data
        for game in games:
            if counter >= max_entries:
                break
            game_date, location = game
            formatted_date = datetime.strptime(game_date, '%Y-%m-%d').date()

            # Get city_id for the location
            cur.execute("SELECT city_id FROM Cities WHERE city_name = ?", (location,))
            city_id = cur.fetchone()[0]

            # Check if weather data already exists
            cur.execute("SELECT * FROM Weather WHERE game_date = ? AND city_id = ?", (formatted_date.strftime('%Y-%m-%d'), city_id))
            existing_data = cur.fetchone()
            if existing_data:
                continue  

            # Fetch weather data from the API
            url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{formatted_date}/{formatted_date}?unitGroup=us&elements={weather_elements}&key={api_key}&contentType=csv&include=days"
            response = requests.get(url)

            if response.status_code == 200:
                print(f"Success: Data for {location} on {formatted_date} fetched successfully.")
                csv_data = response.text.splitlines()
                for row in csv_data[1:]:
                    data = row.split(',')
                    writer.writerow([formatted_date, location] + data[1:])
                    cur.execute("""INSERT OR IGNORE INTO Weather (
                        game_date, 
                        city_id, 
                        max_temp, 
                        min_temp, 
                        precipitation, 
                        wind_speed, 
                        humidity, 
                        uv_index, 
                        conditions
                    ) VALUES (?,?,?,?,?,?,?,?,?)""", 
                    (formatted_date, city_id, data[1], data[2], data[4], data[6], data[3], data[8], data[9]))
                    conn.commit()
                    counter += 1
            else:
                print(f"Error fetching data for {location} on {formatted_date}: {response.status_code}")
                print(f"Error response text: {response.text}")

    print("Weather data for NFL games has been saved to nfl_weather_data.csv.")
    return conn  

def get_max_capacity(city_dict):
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
            
            # Loops thorught each NFL game location in city_dict
            for k,y in city_dict.items():
                # Checks if the current city name matches the city name of a game location
                if city_name == k[0]:
                    # Stores the max capacity of the stadium to the 
                    stadium_dict[city_name] = max_captacity
    #print(stadium_dict)
    #print(city_dict)
    return stadium_dict

def create_database(data_dict, city_dict, stadium_dict, tuple_lst, state_lst):
    # Creates the databse
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + "Final_test.db")
    cur = conn.cursor()
    
    # Creates the database for the city list
    cur.execute(""" CREATE TABLE IF NOT EXISTS Location (number INTEGER, location Text, latitude INTEGER, longitude INTEGER, 
                UNIQUE (number, location)) """)

    # Creates the databsse and adds the header
    cur.execute(""" CREATE TABLE IF NOT EXISTS Games (year INTEGER, month INTEGER, day INTEGER, location INTEGER, attendance INTEGER, capacity INTEGER, 
                UNIQUE (year, month, day, location, attendance, capacity)) """)
    
    #creates the coordinate database
    cur.execute(""" CREATE TABLE IF NOT EXISTS Coordinates (city STRING, state INTEGER, latitude INTEGER, longitude INTEGER, population INTEGER, 
                UNIQUE(city, state, latitude, longitude, population)) """)
    
    cur.execute(""" CREATE TABLE IF NOT EXISTS Coord_Guide (Id INTEGER, state STRING, UNIQUE(Id, state)) """)
    conn.commit()

    # Creates a attendance list to check if the code is getting the attendance correctly
    #attendance_list = []
    data_counter = 0
    maximum = 0

    # Loops throught data_dict to begin adding it to the database
    for (key,value), (tup) in zip(data_dict.items(), tuple_lst):
        #print(key, value)
        # Checks if 25 rows of data have been added and breaks if it is true
        if data_counter == 25:
            break
        else:
            # Gets the integers for the year, month, and day of each NFL game in data_dict
            year = key[0:4]
            month = key[5:7]
            day = key[8:10]        
            location = 0
            key = ""
            # Loops throught city_dict
            for index, answer in city_dict.items():
                # Checks if the current city name within data_dict matches the current city name within city_dict
                index_str = index[0] + index[1][0:1]
                value_str = value[0][0] + value[0][1][0:1]
                #print(value)
                if index_str == value_str:
                    # Loops throught stadium_dict
                    for k,y in stadium_dict.items():
                        # Checks if the city name city name match and set the maximum to y
                        if str(k) == str(index[0]):
                            maximum = y
                    # Assigns a location index to the city
                    location = int(answer)
                    key = index
            # Assigns the attendance of the game to the "attendance" variable
            attendance = value[1]
            #attendance_list.append(attendance)
            # Checks if the row of data already exists within the table of the database.
            if cur.execute("SELECT * FROM Games WHERE year=? AND month=? AND day=? AND location=? AND attendance=? AND capacity=?", (year, month, day, location, attendance, maximum)).fetchall():
                continue
            # Check if the location is valid
            elif location == 0:
                continue
            # Adds the row to the database
            else:
                city = tup[0]
                state = tup[1]
                state_index = state_lst.index(state)
                longitude = tup[2]
                latitude = tup[3]
                population = tup[4]
                #adds the rows already in the database when running the code
                if cur.execute("SELECT * FROM Coordinates WHERE city=? AND state=? AND latitude=? AND longitude=? AND population=?", (city, state_index, latitude, longitude, population)).fetchall():
                    continue
                #adds new rows of data into the database
                else:
                    cur.execute("INSERT OR IGNORE INTO Coordinates (city, state, latitude, longitude, population) VALUES (?,?,?,?,?)", (city, state_index, latitude, longitude, population))
                    cur.execute("INSERT OR IGNORE INTO Coord_Guide (Id, state) VALUES (?, ?)", (state_index, state))
                    conn.commit()
                    #print("inputing data")
                    
                cur.execute("INSERT OR IGNORE INTO Games (year, month, day, location, attendance, capacity) VALUES (?,?,?,?,?,?)", (year, month, day, location, attendance, maximum))
                cur.execute("INSERT OR IGNORE INTO Location (number, location, latitude, longitude) VALUES (?,?,?,?)", (location, str(key), latitude, longitude))
                conn.commit()
                data_counter += 1
    # Joins some data from the "Location" table with the "Games" table
    cur.execute("""SELECT Games.location, Games.year, Games.month, Games.day, Games.attendance, Games.capacity, Location.longitude, Location.latitude 
                FROM Games 
                JOIN Location ON Games.location = Location.number""")
    
    result_list = cur.fetchall()
    # Creates the database containing all of hte information needed for calculation and adds the header
    cur.execute(""" CREATE TABLE IF NOT EXISTS All_Information (location INTEGER, year INTEGER, month INTEGER, day INTEGER, attendance INTEGER, capacity INTEGER, longitude INTEGER, latitude INTEGER, 
                UNIQUE (year, month, day, location, attendance, capacity, latitude, longitude)) """)
    for result in result_list:
        #print(result)
        # Creates new values and assigned the information from the JOIN function to them
        new_location_key = result[0]
        new_year = result[1]
        new_month = result[2]
        new_day = result[3]
        new_attendance = result[4]
        new_max = result[5]
        new_lat = result[6]
        new_long = result[7]
        # Adds the information to the new database
        cur.execute("INSERT OR IGNORE INTO All_Information (location, year, month, day, attendance, capacity, latitude, longitude) VALUES (?,?,?,?,?,?,?,?)", (new_location_key, new_year, new_month, new_day, new_attendance, new_max, new_lat, new_long))
        conn.commit()

def create_graph():
    #visualization
    graph_x = []
    graph_y = []
    labels = []
    
    connection= sqlite3.connect('final_test.db')
    
    cursor_loct = connection.cursor()
    cursor_loct.execute("SELECT * FROM Location")
    rows_loct = cursor_loct.fetchall()
    
    cursor_cap = connection.cursor()
    cursor_cap.execute("SELECT * FROM Games")
    rows_cap = cursor_cap.fetchall()
    
    
    for loct in rows_loct:
        visited = []
        #print(loct)
        loct_id = loct[0]
        loct = loct[1]
        loct_lst = loct.split(',')
        loct_city = loct_lst[0].strip('(').strip("'")
        loct_state = loct_lst[1].strip(')').strip("'")
        loct_state = loct_state.strip(" '")
        location = loct_city + ", " + loct_state
        percent_list = []
        for cap in rows_cap:
            percent = 0.0
            #print(cap)
            cap_id = cap[3]     
            if cap_id == loct_id:
                attendance = cap[4]
                capacity = cap[5]
                percent = (attendance / capacity)
                percent_list.append(percent)
        average = sum(percent_list) / len(percent_list)
        average = int(average * 10000) / 100
        temp_tup = (location, average)
        if temp_tup not in visited:
            graph_x.append(average)
            graph_y.append(location)
            visited.append(temp_tup)

    # Plots the attendance as a bar graph
    print(graph_x)
    print(graph_y)
    plt.barh(graph_y, graph_x)
    # Adds the title and labels to the bar graph
    plt.title("Average attendance percentage for each NFL stadium")
    plt.xlabel("Percentage")
    plt.ylabel("Stadium City Location")

    # Adds the percentage to the end of each bar in the bar graph
    for index in range(len(graph_x)):
        plt.text(graph_y[index], graph_x[index], "top", va="center")
    plt.show()

def create_scatter_graph():
    #visualization
    graph_x = []
    graph_y = []
    labels = []
    
    connection= sqlite3.connect('final_test.db')
    cursor_coor = connection.cursor()
    cursor_coor.execute("SELECT * FROM Coordinates")
    rows_coor = cursor_coor.fetchall()
    
    cursor_loct = connection.cursor()
    cursor_loct.execute("SELECT * FROM Location")
    rows_loct = cursor_loct.fetchall()
    
    cursor_cap = connection.cursor()
    cursor_cap.execute("SELECT * FROM Games")
    rows_cap = cursor_cap.fetchall()
    
    cursor_guide = connection.cursor()
    cursor_guide.execute("SELECT * FROM Coord_Guide")
    rows_guide = cursor_guide.fetchall()
    
    location_lst = []
    for coor in rows_coor:
        state = None
        population = None
        state_num = coor[1]
        for guide in rows_guide:
            if guide[0] == state_num:
                state = guide[1]
                population = coor[4]
                city = coor[0]
        for cap in rows_cap:
            percentage = int((cap[4] / cap[5]) * 10000) / 100
            cap_num = cap[3]
            for loct in rows_loct:
                loct_num = loct[0]
                if cap_num == loct_num:
                    location_str = loct[1]
                    loct_lst = location_str.split(',')
                    loct_city = loct_lst[0].strip('(').strip("'")
                    loct_state = loct_lst[1].strip(')').strip("'")
                    loct_state = loct_state.strip(" '")
                    location = (loct_city, loct_state)
                    temp_tup = (city, state)
                    if temp_tup == location:
                        if location not in location_lst:
                            graph_x = [percentage] + graph_x
                            graph_y = [population] + graph_y
                            labels = [temp_tup] + labels
                            location_lst.append(location)
    for i, label in enumerate(labels):
        plt.annotate(label, (graph_x[i], graph_y[i]), textcoords="offset points", xytext=(5,5), ha='center')
    plt.xlabel("percentage of stadium filled")
    plt.ylabel("population of city")
    plt.scatter(graph_x, graph_y)
    plt.show()
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
            
            
            """ for index in range(0, len(city_list)):
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
                    location = index """
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
                if cur.execute("SELECT * FROM Coordinates WHERE city=? AND state=? AND longitude=? AND latitude=? AND population=?", (city, state_index, longitude, latitude, longitude)).fetchall():
                    continue
                #adds new rows of data into the database
                else:
                    cur.execute("INSERT OR IGNORE INTO Coordinates (city, state, longitude, latitude, population) VALUES (?,?,?,?,?)", (city, state_index, longitude, latitude, longitude))
                    cur.execute("INSERT OR IGNORE INTO Coord_Guide (Id, state) VALUES (?, ?)", (state_index, state))
                    conn.commit()
                    #print("inputing data")
                    
                cur.execute("INSERT OR IGNORE INTO Games (year, month, day, location, attendance, capacity) VALUES (?,?,?,?,?,?)", (year, month, day, location, attendance, maximum))
                cur.execute("INSERT OR IGNORE INTO Location (number, location, latitude, longitude) VALUES (?,?,?,?)", (location, str(key), latitude, longitude))
                conn.commit()
                data_counter += 1
    cur.execute("""SELECT Games.location, Games.year, Games.month, Games.day, Games.attendance, Games.capacity, Location.longitude, Location.latitude 
                FROM Games 
                JOIN Location ON Games.location = Location.number""")
    
    result_list = cur.fetchall()
    # Creates the databsse and adds the header
    cur.execute(""" CREATE TABLE IF NOT EXISTS All_Information (location INTEGER, year INTEGER, month INTEGER, day INTEGER, attendance INTEGER, capacity INTEGER, longitude INTEGER, latitude INTEGER, 
                UNIQUE (year, month, day, location, attendance, capacity, longitude, latitude)) """)
    for result in result_list:
        print(result)
        new_location_key = result[0]
        new_year = result[1]
        new_month = result[2]
        new_day = result[3]
        new_attendance = result[4]
        new_max = result[5]
        new_lat = result[6]
        new_long = result[7]
        cur.execute("INSERT OR IGNORE INTO All_Information (location, year, month, day, attendance, capacity, latitude, longitude) VALUES (?,?,?,?,?,?,?,?)", (new_location_key, new_year, new_month, new_day, new_attendance, new_max, new_lat, new_long))
        conn.commit()
    
        
    
"""     #puts in 25 rows of data into the data base
    for tup in tuple_lst:
        #stops after 25 rows of data are put into the data base
        if data_counter == 25:
            #print("Done with inputing data")
            break
        else:
            city = tup[0]
            state = tup[1]
            state_index = state_lst.index(state)
            longitude = tup[2]
            latitude = tup[3]
            population = tup[4]
            #adds the rows already in the database when running the code
            if cur.execute("SELECT * FROM Coordinates WHERE city=? AND state=? AND longitude=? AND latitude=? AND population=?", (city, state_index, longitude, latitude, population)).fetchall():
                continue
            #adds new rows of data into the database
            else:
                cur.execute("INSERT OR IGNORE INTO Coordinates (city, state, longitude, latitude, population) VALUES (?,?,?,?,?)", (city, state_index, longitude, latitude, population))
                cur.execute("INSERT OR IGNORE INTO Coord_Guide (Id, state) VALUES (?, ?)", (state_index, state))
                conn.commit()
                data_counter += 1
                #print("inputing data")
                
    # Joins the "Games" table and ""
    #cur.execute("SELECT Games.") """
                 


def create_graph(data_dict, stadium_dict):
    # Creates the dicitonaries that will be used for the bar graph
    game_attendance_dict = {}
    average_dict = {}
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
    #print(graph_x)
    #print(graph_y)

    # Plots the attendance as a bar graph
    plt.barh(graph_x, graph_y)
    # Adds the title and labels to the bar graph
    plt.title("Average attendance percentage for each NFL stadium")
    plt.xlabel("Percentage")
    plt.ylabel("Stadium City Location")

    # Adds the percentage to the end of each bar in the bar graph
    for index in range(len(graph_x)):
        plt.text(graph_y[index], graph_x[index], str(graph_y[index]), va="center")

    plt.show()
    
    return average_dict

def create_scatter_graph(tuple_lst, import_dict):
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
        plt.annotate(label, (graph_x[i], graph_y[i]), textcoords="offset points", xytext=(5,5), ha='center')
    plt.title("Average attendance percentage for each NFL stadium")
    plt.xlabel("percentage of stadium filled")
    plt.ylabel("population of city")
    plt.scatter(graph_x, graph_y)
    plt.show()
# Function to create a pie chart for weather conditions
def make_pie_chart(conn):
    cur = conn.cursor()
    cur.execute("SELECT conditions FROM Weather")
    conditions_data = cur.fetchall()
    conditions_list = [condition[0] for condition in conditions_data]

    # Define categories for weather conditions
    def categorize_condition(condition):
        if "rain" in condition.lower():
            return "Rain"
        elif "clear" in condition.lower():
            return "Clear"
        elif "cloudy" in condition.lower():
            return "Cloudy"
        elif "snow" in condition.lower():
            return "Snow"
        else:
            return "Other"

    grouped_conditions = [categorize_condition(condition) for condition in conditions_list]
    condition_counts = {}
    for condition in grouped_conditions:
        if condition in condition_counts:
            condition_counts[condition] += 1
        else:
            condition_counts[condition] = 1

    labels = list(condition_counts.keys())
    sizes = list(condition_counts.values())

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
    plt.title('Percentage of Games with Different Weather Conditions', fontsize=16)
    plt.axis('equal')  
    plt.show()

 # Define games
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
# Define API key and weather elements to fetch
api_key = 'N9DKDVJTSMT2WMRKEJBM7ZQ83'
weather_elements = "datetime,tempmax,tempmin,humidity,precip,preciptype,windspeedmax,windspeedmin,uvindex,description"
max_entries = 25
conn = fetch_weather_data(games, api_key, weather_elements, max_entries)


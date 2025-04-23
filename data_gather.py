import requests
import sqlite3
import os
from bs4 import BeautifulSoup
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
        # Gets the month of the game
        date_month = day["date"][5:7]
        
        # Checks if the game is in the 2023-2024 regular season
        if season_type == 'regular-season' and int(date_month) > 8:
            # Loops throught the details of every game to find the location and attendance
            for game in day["competitions"]:
                # Checks if the city is in the United States and gets the location if it does
                if "state" in game["venue"]["address"].keys():
                    loc_tuple = (game["venue"]["address"]["city"], game["venue"]["address"]["state"])
                # Continues if the location is not within the states
                else:
                    continue
                    #loc_tuple = (game["venue"]["address"]["city"], game["venue"]["address"]["country"])
                # Adds the location and attendance number to data_dict
                data_dict[day["date"]] = [loc_tuple, game['attendance']]
                # Adds the location to city_list. Does skip over duplicates
                if loc_tuple not in city_list:
                    city_list.append(loc_tuple)
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
            if city_line:
                city = city[:-3]
            state = box[1].getText().strip()
            if state not in state_lst:
                state_lst.append(state)
            population = box[2].getText().strip()

        #find the latitude and longitude of the city
        coordinates = city_info.find_all('span', class_ = 'geo')
        if len(coordinates) != 0:
            cor = coordinates[0].getText().split(';')
            latitude = cor[0].strip()
            longitude = cor[1].strip()
            #Create the tuple
            loct_tup = (city, state, latitude, longitude, population)
            my_tup = (city, state)
            cord_dict[my_tup] = index
            index += 1
            tuple_lst.append(loct_tup)
    return [tuple_lst, state_lst, cord_dict]

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
            # Creates two variables to store the city name and the max capacity of each NFL stadium
            city_name = capacity[2].getText().strip("\n").split(",")[0]
            max_captacity = int(capacity[3].getText().strip("\n").replace(",", ""))
            
            # Loops thorught each NFL game location in city_dict
            for k,y in city_dict.items():
                # Checks if the current city name matches the city name of a game location
                if city_name == k[0]:
                    # Stores the max capacity of the stadium to the 
                    stadium_dict[city_name] = max_captacity
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
    
    # Create the Weather table with location_id column (replaces city_id)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Weather (
            game_date TEXT, 
            location_id INTEGER, 
            max_temp REAL, 
            min_temp REAL, 
            precipitation REAL, 
            wind_speed REAL, 
            humidity REAL, 
            uv_index INTEGER, 
            conditions TEXT,
            FOREIGN KEY (location_id) REFERENCES Location (location_id),
            UNIQUE(game_date, location_id)
        )
    """)
    
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
        
# Define games
def game_data():
    games = []
    connection = sqlite3.connect('Final_test.db')
    cursor_all = connection.cursor()
    cursor_all.execute("SELECT * FROM Games")
    rows_all = cursor_all.fetchall()

    cursor_location = connection.cursor()
    cursor_location.execute("SELECT * FROM Location")
    rows_location = cursor_location.fetchall()

    for row in rows_all:
        year = row[0]
        month = row[1]
        day = row[2]
        date = f"{year}-{month}-{day}"
        location_num = row[3]
        for location in rows_location:
            first = location[0]
            if location_num == first:
                locat_lst = location[1].split(',')
                first_half = locat_lst[0].strip("('")
                city = first_half
                temp_tup = (date, city)
                games.append(temp_tup)
    return games
        
def fetch_weather_data(games, api_key, weather_elements, max_entries):
    # Connect to the database created by create_database
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + "Final_test.db")
    cur = conn.cursor()

    # Create the Weather table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Weather (
            game_date TEXT, 
            location_id INTEGER, 
            max_temp REAL, 
            min_temp REAL, 
            precipitation REAL, 
            wind_speed REAL, 
            humidity REAL, 
            uv_index INTEGER, 
            conditions TEXT,
            FOREIGN KEY (location_id) REFERENCES Location (location_id),
            UNIQUE(game_date, location_id)
        )
    """)
    conn.commit()

    # Insert location data into the Location table
    location_list = [game[1] for game in games]
    location_list = list(set(location_list))  # Remove duplicates

    for location in location_list:
        # Insert unique locations into the Location table
        cur.execute("""
            INSERT OR IGNORE INTO Location (location) 
            VALUES (?)
        """, (location,))
    conn.commit()

    counter = 0
    with open('nfl_weather_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Game Date', 'Location', 'Max Temperature (F)', 
            'Min Temperature (F)', 'Precipitation (inches)', 
            'Wind Speed (mph)', 'Humidity (%)', 'UV Index', 'Conditions'
        ])

        # Loop through the games and fetch weather data
        for game in games:
            if counter >= max_entries:
                break

            game_date, location_name = game
            formatted_date = datetime.strptime(game_date, '%Y-%m-%d').date()

            # Get the location_id for the location_name
            cur.execute("SELECT location FROM Location WHERE location = ?", (location_name,))
            location_id = cur.fetchone()[0]

            # Check if weather data already exists for this game and location
            cur.execute("""
                SELECT * FROM Weather WHERE game_date = ? AND location_id = ?
            """, (formatted_date.strftime('%Y-%m-%d'), location_id))
            existing_data = cur.fetchone()
            if existing_data:
                continue  # Skip if the data already exists

            # Fetch weather data from the API
            url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location_name}/{formatted_date}/{formatted_date}?unitGroup=us&elements={weather_elements}&key={api_key}&contentType=csv&include=days"
            response = requests.get(url)

            if response.status_code == 200:
                csv_data = response.text.splitlines()
                for row in csv_data[1:]:
                    data = row.split(',')
                    writer.writerow([formatted_date, location_name] + data[1:])
                    # Insert the weather data into the Weather table
                    cur.execute("""
                        INSERT OR IGNORE INTO Weather (
                            game_date, location_id, max_temp, min_temp, 
                            precipitation, wind_speed, humidity, uv_index, conditions
                        ) VALUES (?,?,?,?,?,?,?,?,?)
                    """, (
                        formatted_date, location_id, data[1], data[2], 
                        data[4], data[6], data[3], data[8], data[9]
                    ))
                    conn.commit()
                    counter += 1
            else:
                print(f"Error fetching data for {location_name} on {formatted_date}: {response.status_code}")
                print(f"Error response text: {response.text}")

    return conn
import sqlite3
import matplotlib.pyplot as plt
import numpy as np 
import seaborn as sns
from data_gather import *

def create_graph():
    # Lists for the x and y axis
    graph_x = []
    graph_y = []
    
    connection= sqlite3.connect('final_test.db')
    
    # Pulls data from the Location table in the database
    cursor_loct = connection.cursor()
    cursor_loct.execute("SELECT * FROM Location")
    rows_loct = cursor_loct.fetchall()
    
    # Pulls data from the Games table in the database
    cursor_cap = connection.cursor()
    cursor_cap.execute("SELECT * FROM Games")
    rows_cap = cursor_cap.fetchall()
    
    for loct in rows_loct:
        visited = []
        loct_id = loct[0]
        loct = loct[1]
        loct_lst = loct.split(',')
        if len(loct_lst) > 1:
            loct_city = loct_lst[0].strip('(').strip("'")
            loct_state = loct_lst[1].strip(')').strip("'")
            loct_state = loct_state.strip(" '")
            location = loct_city + ", " + loct_state
            percent_list = []
            # Loops through row_cap and creates a list of attendance percentage for each location
            for cap in rows_cap:
                percent = 0.0
                cap_id = cap[3]     
                if cap_id == loct_id:
                    attendance = cap[4]
                    capacity = cap[5]
                    percent = (attendance / capacity)
                    percent_list.append(percent)
            # Calculates the average attendance percentage for each location
            average = sum(percent_list) / len(percent_list)
            average = int(average * 10000) / 100
            temp_tup = (location, average)
            # Adds a unique temp_tup to the visited list
            if temp_tup not in visited:
                graph_x.append(average)
                graph_y.append(location)
                visited.append(temp_tup)

    # Plots the attendance as a bar graph
    plt.barh(graph_y, graph_x)
    # Adds the title and labels to the bar graph
    plt.title("Average attendance percentage for each NFL stadium")
    plt.xlabel("Percentage")
    plt.ylabel("Stadium City Location")

    # Adds the percentage to the end of each bar in the bar graph
    for i, (location, percent) in enumerate(zip(graph_y, graph_x)):
        # Add a little space to the right of the bar to position the label
        plt.text(percent + 1, i, f"{percent:.2f}%", va='center')
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
    
def create_weather_attendance_graph(conn):
    # Query the Weather and Games tables to get weather conditions and attendance data
    cur = conn.cursor()
    cur.execute("""
    SELECT conditions, AVG(attendance)
    FROM Weather
    JOIN Games ON Weather.location_id = Games.location
    GROUP BY conditions
    """)
    weather_attendance_data = cur.fetchall()

    # Process the data into a dictionary: key = weather condition, value = list of attendance
    weather_attendance = {}

    for condition, attendance in weather_attendance_data:
        # Categorize weather conditions into broader categories
        if "rain" in condition.lower():
            condition_category = "Rain"
        elif "clear" in condition.lower():
            condition_category = "Clear"
        elif "cloudy" in condition.lower():
            condition_category = "Cloudy"
        elif "snow" in condition.lower():
            condition_category = "Snow"
        else:
            condition_category = "Other"
        
        # Add the attendance to the list of the corresponding weather condition category
        if condition_category not in weather_attendance:
            weather_attendance[condition_category] = []
        
        weather_attendance[condition_category].append(attendance)
    
    # Calculate the average attendance for each weather condition
    average_attendance = {condition: np.mean(attendances) for condition, attendances in weather_attendance.items()}
    
    # Prepare data for the graph
    conditions = list(average_attendance.keys())
    avg_attendance = list(average_attendance.values())
    
    sns.set(style="whitegrid")  # Set a seaborn style
    plt.figure(figsize=(10,6))  # Increase figure size for better visibility
    plt.bar(conditions, avg_attendance, color=sns.color_palette("coolwarm", len(conditions)))  # Use coolwarm color palette
    
    # Add labels and title with customized fonts
    plt.xlabel('Weather Condition', fontsize=14, fontweight='bold')
    plt.ylabel('Average Attendance', fontsize=14, fontweight='bold')
    plt.title('Average Attendance per Weather Condition in NFL Games', fontsize=16, fontweight='bold')
    
    # Display the plot with rotated labels and tight layout
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

# Define API key and weather elements to fetch
api_key = 'N9DKDVJTSMT2WMRKEJBM7ZQ83'
weather_elements = "datetime,tempmax,tempmin,humidity,precip,preciptype,windspeedmax,windspeedmin,uvindex,description"
max_entries = 25
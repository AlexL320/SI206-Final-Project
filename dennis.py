import requests
import json
monday_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=2023"
monday_dict = requests.get(monday_url)
monday_data = monday_dict.json()
monday_att = monday_data["events"]
id_list = []
for day in monday_att:
    #print(day["competitions"])
    for game in day["competitions"]:
        id = game["id"]
        print(id)
        print("__________________________________")
        if id not in id_list:
            print(game["attendance"])
            id_list.append(id)
            #print(game["venue"]["address"])
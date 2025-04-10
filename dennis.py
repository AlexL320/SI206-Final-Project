import requests
import json
monday_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=2023"
monday_dict = requests.get(monday_url)
monday_data = monday_dict.json()
monday_att = monday_data["events"]
city_list = []
count = 0
for day in monday_att:
    season_type = day["season"]['slug']
    #print(day["season"])
    date_month = day["date"][5:7]
    #Checks if the game is in the 2023-2024 regular season
    if season_type == 'regular-season' and int(date_month) > 8 and count < 101:
        print(day["date"])
        for game in day["competitions"]:
            print(game["id"])
            #print("__________________________________")
            #print(game["attendance"])
            #print(game["venue"]["address"]["city"])
            if "state" in game["venue"]["address"].keys():
                loc_tuple = (game["venue"]["address"]["city"], game["venue"]["address"]["state"])
            else:
                loc_tuple = (game["venue"]["address"]["city"], game["venue"]["address"]["country"])
            print(loc_tuple)
            if loc_tuple not in city_list:
                city_list.append(loc_tuple)
        count += 1
        print(count)
print(city_list)
from dennis import *

data_list = ()
data_list = get_game_data()
#print(data_dict)

max_capacity = get_max_capacity(data_list[1])
#print(max_capacity)

create_database(data_list[0], data_list[1], max_capacity)

create_graph(data_list[0], max_capacity)
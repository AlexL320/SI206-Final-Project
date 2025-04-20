from dennis import *
from alex_main import *

data_list = ()
data_list = get_game_data()
#print(data_dict)

max_capacity = get_max_capacity(data_list[1])
#print(max_capacity)

create_database(data_list[0], data_list[1], max_capacity)

im_dict = create_graph(data_list[0], max_capacity)

wiki_data = get_wiki_data()[0]
state_list = get_wiki_data()[1]
create_location_database(wiki_data, state_list)
create_scatter_graph(wiki_data, im_dict)

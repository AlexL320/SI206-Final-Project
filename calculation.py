from final_file import *
from landons import *

data_list = ()
data_list = get_game_data()
#print(data_list)

wiki_data = get_wiki_data()[0]
state_list = get_wiki_data()[1]
city_dict = get_wiki_data()[2]

max_capacity = get_max_capacity(city_dict)

#create_database(data_list[0], city_dict, max_capacity, wiki_data, state_list)
print(create_database(data_list[0], city_dict, max_capacity, wiki_data, state_list))

im_dict = create_graph(data_list[0], max_capacity)

create_scatter_graph(wiki_data, im_dict)

make_pie_chart(conn)

#imports
import pandas
import numpy as np
import geopy.distance
import random
import json
import os
import shutil
import folium
import folium.plugins

# Generate initial positions
def generate_users(count, bounding_box):
    data = []
    if bounding_box == None or len(bounding_box) < 4:
        bounding_box = [-90,-180,90,180]

    for _ in range(count):
        data.append([random.uniform(bounding_box[0],bounding_box[2]),random.uniform(bounding_box[1],bounding_box[3])])

    return pandas.DataFrame(data,columns=['Latitude','Longitude'])

# Import initial posistions
def get_users_from_csv(file_path):
    return pandas.read_csv(file_path)
    
def set_range(users, max_range,min_range):
    [random.randrange(min_range,max_range) for i in range(len(users))]
    ranges = [random.randrange(min_range,max_range) for i in range(len(users))]
    users['Range'] = ranges

def calc_bounding_box(users):
    bounding_box = [users["Latitude"].min(),users["Longitude"].min(),users["Latitude"].max(),users["Longitude"].max()]
    return bounding_box

def is_connected(x,y):
    result = 0
    distance = geopy.distance.geodesic((x['Latitude'],x['Longitude']), (y['Latitude'],y['Longitude'])).m
    if distance <= x['Range'] and distance <= y['Range']:
        result = 1
    return result

# Create communication graph
def get_graph(users):
    connections = users.apply(lambda x: [is_connected(x,users.loc[idx]) for idx in range(x.name, len(users))], axis=1)
    lst = connections.values.tolist()
    pad = len(max(lst, key=len))
    com_graph = np.array([[0]*(pad-len(i)) + i for i in lst])
    com_graph = com_graph + com_graph.T - np.diag(np.diag(com_graph))
    return com_graph

# Adjust user positions
# 1 meter ~ 0.00001 degrees
def change_lat_long(prev_value, max_change_m, bounding_box, is_lat):
    new_location = prev_value + random.randrange(-1*max_change_m//2,max_change_m//2)*0.00001
    if bounding_box != None:
        if is_lat:
            if new_location > bounding_box[2]:
                return bounding_box[2]
            elif new_location < bounding_box[0]:
                return bounding_box[0]
        else:
            if new_location > bounding_box[3]:
                return bounding_box[3]
            elif new_location < bounding_box[1]:
                return bounding_box[1]
    return new_location

def move_users(users, max_change_m, bounding_box, use_bounding):
    if not use_bounding:
        bounding_box = None

    users["Latitude"] = users["Latitude"].apply(change_lat_long,args=(max_change_m, bounding_box, True))
    users["Longitude"] = users["Longitude"].apply(change_lat_long,args=(max_change_m, bounding_box, False))

# Output iteration files
# Plot charts
def get_edge_positions(users,graph):
    result = []
    pos_dict = users[['Latitude','Longitude']].to_dict(orient='index')

    for i in range(len(graph)-1):
        for j in range(i+1,len(graph[i])):
            if graph[i][j] == 1:
                point1 = (pos_dict[i]['Latitude'],pos_dict[i]['Longitude'])
                point2 = (pos_dict[j]['Latitude'],pos_dict[j]['Longitude'])
                result.append([point1,point2])

    return result    

def plot_charts(data, output_dir = None):
    users = data['users']
    graph = data['com_graph']    
    # Plot user locations
    fig1 = folium.Map([users.Latitude.mean(),users.Longitude.mean(),], zoom_start=16)
    for latitude, longitude, range in zip(users.Latitude, users.Longitude, users.Range):
        folium.vector_layers.Circle(
            location=[latitude, longitude],
            radius = 3,
            color = '#0e35cf',
            fill=True,
            fill_color='#0e35cf',
            fill_opacity=1
        ).add_to(fig1)
    fig1.save(os.path.join(output_dir,'users.html'))

    # Plot user locations plus range circle
    for latitude, longitude, range in zip(users.Latitude, users.Longitude, users.Range):
        if(random.randrange(0,10) > 7):
            folium.vector_layers.Circle(
                location=[latitude, longitude],
                radius = range,
                color = '#ed2f00',
                fill=True,
                fill_color='#ed2f00',
                weight = 1,
                fill_opacity=.05
            ).add_to(fig1)
    
    fig1.save(os.path.join(output_dir,'users_range.html'))

    # Plot user locations plus graph edges
    fig3 = folium.Map([users.Latitude.mean(),users.Longitude.mean(),], zoom_start=16)
    for latitude, longitude, range in zip(users.Latitude, users.Longitude, users.Range):
        folium.vector_layers.Circle(
            location=[latitude, longitude],
            radius = 3,
            color = '#0e35cf',
            fill=True,
            fill_color='#0e35cf',
            fill_opacity=1
        ).add_to(fig3)

    edges = get_edge_positions(users,graph)
    for edge in edges:
        folium.PolyLine(
            edge,
            weight=1.5,
            color = '#ed2f00',
            opacity = .5
        ).add_to(fig3)

    fig3.save(os.path.join(output_dir,'users_edges.html'))

def save_iteration_files(output, path, include_plots):
    for itr in range(len(output)):
        iter_path = os.path.join(path,str(itr + 1))
        os.mkdir(iter_path)

        users_path = os.path.join(iter_path,"users.csv")
        output[itr]["users"].to_csv(users_path, index=False)

        com_graph_path = os.path.join(iter_path,"com_graph.csv")
        np.savetxt(com_graph_path, output[itr]['com_graph'], delimiter=",")

        if include_plots:
            plot_charts(output[itr], iter_path)

# Output json
def save_json(output,path):
    prepped_output = []
    for iter in output:
        prepped_output.append({"users":iter['users'].to_json(orient="split"),"com_graph":iter['com_graph'].tolist()})

    json_output = json.dumps(prepped_output)
    file_path = os.path.join(path,"output.json")
    with open(file_path,"w") as outfile:
        outfile.write(json_output)

def save_files(output, path, include_plots):
    path = os.path.join(path,"output")
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    save_json(output, path)
    save_iteration_files(output, path, include_plots)

def generate_data(initial_dataset, user_count, use_bounding, bounding_box, min_range,max_range, iterations, max_move):
    # Create initial positions and range
    if initial_dataset:
        users = get_users_from_csv(initial_dataset)
        if use_bounding and (bounding_box == None or len(bounding_box) < 4):
            bounding_box = calc_bounding_box(users)
    else:
        users = generate_users(user_count,bounding_box)
    set_range(users, max_range,min_range)

    output = []

    for _ in range(iterations):
        graph = get_graph(users)
        output.append({"users":users.copy(),"com_graph":graph})
        move_users(users,max_move,bounding_box,use_bounding)
    return output

def main():
    # PARAMETERS
    # CSV file containing columns for "Latitude" and "Longitude" of users initial positions
    initial_dataset = ""
    # The user count if users are generated (ignored if using initial_dataset)
    user_count = 500
    # Restrict users to a specific area
    use_bounding = False
    # Maximum space that users can exist in (min latitude, min longitude, max latitude, max longitude)
    # Used to generate users if initial_dataset is empty
    # Used to restrict user movement if use_bounding = True
    bounding_box = [33.414585,-111.939926,33.430918,-111.926184]
    # Distance that users can communicate with other users (in meters)
    min_range = 180
    max_range = 200
    # How many iterations of user movement and communication graph generation
    iterations = 4
    # How far a user can move each iteration (in meters)
    max_move = 50
    # Folder to save output files
    output_folder = os.getcwd()
    # Include plots of users for each iteration
    include_plots = True

    output = generate_data(initial_dataset, user_count, use_bounding, bounding_box, min_range, max_range, iterations, max_move)
    save_files(output,output_folder,include_plots)

if __name__ == "__main__":
    main()
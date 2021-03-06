# Author: Mees Altena, 24-04-2020
# Licence: MIT 
import re
import os
import requests
import folium
from folium.plugins import HeatMap
import ipinfo
import sys
import time
from collections import Counter
import operator

# Set a default api key here if you're not using sys arguments.
api_key = ""

# Filename of the txt with the output of: grep "Failed password" /var/log/auth.log > filename.txt
try:
    filename = sys.argv[1]
except IndexError:
    filename = "failed_logins.txt"
    pass

# ipinfo.io api key
try:
    api_key = sys.argv[2]
except IndexError:
    if(api_key == ""):
        raise IndexError("API key not found. Please pass your ipinfo.io api key as the second argument, or set it manually.")

# minimum login attempts per ip required to include it in the heatmap
try:
    min_attempts = int(sys.argv[3])
except IndexError:
    min_attempts = 30
    pass    

# what filename the heatmap should be saved as.
try:
    heatmap_filename = sys.argv[4]
except IndexError:
    heatmap_filename = 'heatmap.html'
    pass

# create handler to interface with API
ip_handler = ipinfo.getHandler(api_key)

# read the file, split on newlines into array, return list of ips
def read_file_get_ips(filename):
    with open(filename) as f:
        f_a = f.read().split('\n')
        # get array with only the ips 
        # TODO: Use a regex to match and extract ips
        ips = [x[x.find('from ')+5:x.find(' port')] for x in f_a]

        # remove all empty strings, theres probably a better way to do this
        while('' in ips):
            ips.remove('')
        
        print('Read file ' + filename + ' and got ' + str(len(ips)) + ' login attempts.')
        return ips

# Returns a list with the items in the passed list that occur at least min_attempts times.
def get_applicable_ips(ips):
    counts = Counter(ips).most_common()
    meet_minimum = [x[0] for x in counts if x[1] > min_attempts]
    print('No. of ips with at least ' + str(min_attempts) + ' login attempts: ' + str(len(meet_minimum)))
    return meet_minimum

# Call ipinfo api per api to get coordinates.
def get_ip_coordinates(ips):
    
    print('Fetching coordinates...')
    if(len(ips) > 500):
        print("Fetching coordinates for > 500 IP's. Please consider using your own (free) ipinfo API key.")

    # split the list of ips into batches of 100 (or less, if the list is smaller)
    batches = [ips[x:x+100] for x in range(0, len(ips), 100)]
    coords = []
    start = time.process_time()
    for batch in batches:
        # append /loc to each ip to get only the location info from the api
        b = [x + "/loc" for x in batch]
        # send the request to the api and get the values as a list
        v = list(ip_handler.getBatchDetails(b).values())
        # split the coords into a list with lat and lon if type is not dict, because the type of an error response is a dict
        c = [x.split(',') for x in v if not isinstance(x, dict)]
        coords.extend(c)
        print("Fetched " + str(len(coords)) + "/" + str(len(ips)) + " coordinates in " + str(round(time.process_time() - start, 3)) + " seconds.")
    
    return coords       

def generate_and_save_heatmap(coords):        
    # generate and save heatmap
    m = folium.Map(tiles="OpenStreetMap", location=[20,10], zoom_start=2)
    # mess around with these values to change how the heatmap looks
    HeatMap(data = coords, radius=15, blur=20, max_zoom=2, max_val=2).add_to(m)
    m.save(heatmap_filename) 
    print('Done. heatmap saved as ' + heatmap_filename)  
    return

def main():    
    ips = read_file_get_ips(filename)
    ips_count = get_applicable_ips(ips)
    coords = get_ip_coordinates(ips_count)
    generate_and_save_heatmap(coords)

main()
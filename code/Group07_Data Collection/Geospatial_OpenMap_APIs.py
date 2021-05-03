from concurrent.futures import ThreadPoolExecutor
import csv
import datetime
import logging
import pandas as pd
import os
import random
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time

## CONSTANTS: Dataset Name
DATA_SET_DIRECTORY = './'
FILE_NAME = 'airbnb_listings.csv'
FILE_NAME_CONCATENATED = 'concatenated_listings.csv'
FILE_NAME_MISSING_FROM_ROUND1 = 'missing_listings.csv'
FILE_NAME_UNIQUE_ID_COORDINATES = 'unique_listings_{id}.csv'
FILE_NAME_MISSING_ID_COORDINATES = 'missing_listings_{id}.csv'
INPUT_FOLDER_NAME_UNIQUE_LISTINGS = 'unique_listings'
OUTPUT_FOLDER_NAME_UNIQUE_LISTINGS = 'unique_listings/output'
UNIQUE_LISTINGS_DATA_SET_LATITUDE_INDEX = 6 #3
UNIQUE_LISTINGS_DATA_SET_LONGITUDE_INDEX = 7 #4
DATA_SET_DATE_TIME_FORMAT = '%Y-%m-%d'
DATA_DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

## For Extraction
NUM_DATA_SETS = 1 #6
NUM_THREADS = 2
MAX_RETRIES = 100
VAL_IF_NOT_FOUND = -1
SLEEP_DURATION = 5

## For Overpass
OVERPASS_URL = "https://overpass.nchc.org.tw/api/interpreter"
OVERPASS_URL_1 = "https://overpass.nchc.org.tw/api/interpreter"
OVERPASS_URL_2 = "https://overpass.kumi.systems/api/interpreter"
OVERPASS_URL_3 = "https://lz4.overpass-api.de/api/interpreter"
OVERPASS_URL_4 = "https://overpass.kumi.systems/api/interpreter"

OVERPASS_QUERY_AMENITY_ALL = """[out:json];
area[name="Singapore"];
(node["amenity"="{amenity}"](area);
 way["amenity"="{amenity}"](area);
 rel["amenity"="{amenity}"](area);
);
out center;"""

OVERPASS_QUERY_SUBWAY_ALL = """[out:json];
area[name="Singapore"];
node(area)[railway=station][station=subway];
out center;"""

OVERPASS_QUERY_BUS_STOP_ALL = """[out:json];
area[name="Singapore"];
node(area)[public_transport=stop_position][bus=yes];
out center;"""

OVERPASS_QUERY_AMENITY = """[out:json];
(node["amenity"="{amenity}"](around:{radius},{latitude},{longitude});
 way["amenity"="{amenity}"](around:{radius},{latitude},{longitude});
 rel["amenity"="{amenity}"](around:{radius},{latitude},{longitude});
);
out center;"""

OVERPASS_QUERY_SHOP = """[out:json];
(node["shop"="convenience"](around:{radius},{latitude},{longitude});
 way["shop"="convenience"](around:{radius},{latitude},{longitude});
 rel["shop"="convenience"](around:{radius},{latitude},{longitude});
 node["shop"="dairy"](around:{radius},{latitude},{longitude});
 way["shop"="dairy"](around:{radius},{latitude},{longitude});
 rel["shop"="dairy"](around:{radius},{latitude},{longitude});
 node["shop"="department_store"](around:{radius},{latitude},{longitude});
 way["shop"="department_store"](around:{radius},{latitude},{longitude});
 rel["shop"="department_store"](around:{radius},{latitude},{longitude});
 node["shop"="general"](around:{radius},{latitude},{longitude});
 way["shop"="general"](around:{radius},{latitude},{longitude});
 rel["shop"="general"](around:{radius},{latitude},{longitude});
 node["shop"="mall"](around:{radius},{latitude},{longitude});
 way["shop"="mall"](around:{radius},{latitude},{longitude});
 rel["shop"="mall"](around:{radius},{latitude},{longitude});
 node["shop"="supermarket"](around:{radius},{latitude},{longitude});
 way["shop"="supermarket"](around:{radius},{latitude},{longitude});
 rel["shop"="supermarket"](around:{radius},{latitude},{longitude});
);
out center;"""

OVERPASS_QUERY_TOURISM = """[out:json];
(node["tourism"="attraction"](around:{radius},{latitude},{longitude});
 way["tourism"="attraction"](around:{radius},{latitude},{longitude});
 rel["tourism"="attraction"](around:{radius},{latitude},{longitude});
);
out center;"""

OVERPASS_QUERY_BUS_STOP = """[out:json];
(node(around:{radius},{latitude},{longitude})[highway=bus_stop];
way(around:{radius},{latitude},{longitude})[highway=bus_stop];
rel(around:{radius},{latitude},{longitude})[highway=bus_stop];
);
out center;"""

OVERPASS_QUERY_SUBWAY = """[out:json];
(node(around:{radius},{latitude},{longitude})[railway=station][station=subway];
way(around:{radius},{latitude},{longitude})[railway=station][station=subway];
rel(around:{radius},{latitude},{longitude})[railway=station][station=subway];
);
out center;"""

MIN_RADIUS = 200  # 200 metres
MAX_RADIUS = 1000  # 1000 metres

QUERY_CAFE = 'cafe'
QUERY_RESTAURANT = 'restaurant'

def get_url():
    urls = (OVERPASS_URL, OVERPASS_URL_1, OVERPASS_URL_2, OVERPASS_URL_3, OVERPASS_URL_4)
    index = random.randrange(len(urls))

    return urls[2] #index

def requests_retry_session(retries=MAX_RETRIES, backoff_factor=0.3, status_forcelist=(429, 500, 502, 504), session=None):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_subway_all():
    session = requests_retry_session()
    response = session.get(get_url(), params={'data': OVERPASS_QUERY_SUBWAY_ALL})
    #logger.debug('Response for get_subway_all: %s', response.status_code)
    data = response.json()
    if response.status_code == 429:
        logger.info("Too many requests: %s", data)
    elems = data.get('elements')
    return (len(elems))


def get_busstop_all():
    session = requests_retry_session()
    response = session.get(get_url(), params={'data': OVERPASS_QUERY_BUS_STOP_ALL})
    logger.debug('Response for get_busstop_all: %s', response.status_code)
    data = response.json()
    if response.status_code == 429:
        logger.info("Too many requests: %s", data)
    elems = data.get('elements')
    # pprint.pprint(elems)
    return (len(elems))


def get_amenity_count(latitude, longitude, amenity, radius=MAX_RADIUS):
    session = requests_retry_session()
    query_built = OVERPASS_QUERY_AMENITY.format(amenity=amenity, radius=radius, latitude=latitude, longitude=longitude)
    response = session.get(get_url(), params={'data': query_built})
    #logger.debug('Response for get_amenity_count: %s', response.status_code)
    data = response.json()
    if response.status_code == 429:
        logger.info("Too many requests: %s", data)
    elems = data.get('elements')
    # pprint.pprint(elems)
    return (len(elems))


def get_shop_count(latitude, longitude, radius=MAX_RADIUS):
    session = requests_retry_session()
    query_built = OVERPASS_QUERY_SHOP.format(radius=radius, latitude=latitude, longitude=longitude)
    response = session.get(get_url(), params={'data': query_built})
    #logger.debug('Response for get_shop_count: %s', response.status_code)
    data = response.json()
    if response.status_code == 429:
        logger.info("Too many requests: %s", data)
    elems = data.get('elements')
    set_elems = set()
    for elem in elems:
        set_elems.add(elem.get('id'))
    # pprint.pprint(set_elems)
    return (len(set_elems))


def get_tourist_attractions_count(latitude, longitude, radius=MAX_RADIUS):
    session = requests_retry_session()
    query_built = OVERPASS_QUERY_TOURISM.format(radius=radius, latitude=latitude, longitude=longitude)
    response = session.get(get_url(), params={'data': query_built})
    #logger.debug('Response for get_tourist_attractions_count: %s', response.status_code)
    data = response.json()
    if response.status_code == 429:
        logger.info("Too many requests: %s", data)
    elems = data.get('elements')
    set_elems = set()
    for elem in elems:
        set_elems.add(elem.get('id'))
    # pprint.pprint(set_elems)
    return (len(set_elems))


def get_public_transport_count(latitude, longitude, query, radius=MAX_RADIUS):
    session = requests_retry_session()
    response = session.get(get_url(),
                           params={'data': query.format(radius=radius, latitude=latitude, longitude=longitude)})
    #logger.debug('Response for get_public_transport_count: %s', response.status_code)
    data = response.json()
    if response.status_code == 429:
        logger.info("Too many requests: %s", data)
    elems = data.get('elements')
    # pprint.pprint(elems)
    return (len(elems))

def extractLocationFeatures(threadId=0, input_file_name=os.path.join(DATA_SET_DIRECTORY, FILE_NAME)):
    '''
    Extract Location features
    :type threadId: object
    '''
    # logger.info('Thread ID: %s Reading input file: %s', threadId, input_file_name)
    file_name = input_file_name.split('/')[-1]
    output_file_name = DATA_SET_DIRECTORY + OUTPUT_FOLDER_NAME_UNIQUE_LISTINGS + '/' + file_name.replace('.csv', '') + '_location.csv'
     
    print('Thread ID:', threadId, 'Reading input file:', input_file_name, 'Output File Name: ', output_file_name)

    with open(input_file_name, encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file) #, delimiter=','
        line_count = 0
        new_rows = []
        #print('Rows in file: %s', fileName, len(csv_reader))
        for row in csv_reader:
            if(line_count == 0):
                line_count += 1
                
                print(line_count, 'Current Column names are: ', row)
                new_headers = ['Subway_Count_Within_200m', 'Subway_Count_Within_1000m',
                               'Bus_Count_Within_200m', 'Bus_Count_Within_1000m',
                               'Restaurants_Count_Within_200m', 'Restaurants_Count_Within_1000m',
                               # 'Cafes_Count_Within_200m', 'Cafes_Count_Within_1000m',
                               'Shops_Count_Within_200m', 'Shops_Count_Within_1000m',
                               'Attractions_Count_Within_200m', 'Attractions_Count_Within_1000m']
                row.extend(new_headers)
                proximity_df = pd.DataFrame(columns = row)	

            elif(line_count > 0):
                line_count += 1                
                latitude = row[UNIQUE_LISTINGS_DATA_SET_LATITUDE_INDEX]
                longitude = row[UNIQUE_LISTINGS_DATA_SET_LONGITUDE_INDEX]
                retries = 0
                while retries < MAX_RETRIES:
                    try:
                        print('ThreadId:', threadId, ' Line Count:', line_count)
                        #logger.debug('Thread ID: %s, Extracting Subway Counts for line: %s', threadId, line_count)
                        count_subway_200m = get_public_transport_count(latitude, longitude, OVERPASS_QUERY_SUBWAY,
                                                                       MIN_RADIUS)
     
                        count_subway_1000m = get_public_transport_count(latitude, longitude, OVERPASS_QUERY_SUBWAY,
                                                                        MAX_RADIUS)
                        #logger.debug('Thread ID: %s, Subway Counts for line: %s = %s in 200m, %s in 1000m',
                        #             threadId,
                        #             line_count, count_subway_200m, count_subway_1000m)

                        #logger.debug('Thread ID: %s, Extracting Bus Stop Counts for line: %s', threadId, line_count)
                        count_bus_stop_200m = get_public_transport_count(latitude, longitude, OVERPASS_QUERY_BUS_STOP,
                                                                         MIN_RADIUS)
                        count_bus_stop_1000m = get_public_transport_count(latitude, longitude, OVERPASS_QUERY_BUS_STOP,
                                                                          MAX_RADIUS)
                        #logger.debug('Thread ID: %s, Bus Stop  Counts for line: %s = %s in 200m, %s in 1000m',
                        #             threadId,
                        #             line_count, count_bus_stop_200m, count_bus_stop_1000m)

                        #logger.debug('Thread ID: %s, Extracting Restaurant Counts for line: %s', threadId, line_count)
                        count_restaurant_200m = get_amenity_count(latitude, longitude, QUERY_RESTAURANT, MIN_RADIUS)
                        count_restaurant_1000m = get_amenity_count(latitude, longitude, QUERY_RESTAURANT, MAX_RADIUS)
                        #logger.debug('Thread ID: %s, Restaurant Counts for line: %s = %s in 200m, %s in 1000m',
                        #             threadId,
                        #             line_count, count_restaurant_200m, count_restaurant_1000m)

                        # count_cafe_200m = get_amenity_count(latitude, longitude, QUERY_CAFE, MIN_RADIUS)
                        # count_cafe_1000m = get_amenity_count(latitude, longitude, QUERY_CAFE, MAX_RADIUS)

                        #logger.debug('Thread ID: %s, Extracting Shop Counts for line: %s', threadId, line_count)
                        count_shop_200m = get_shop_count(latitude, longitude, MIN_RADIUS)
                        count_shop_1000m = get_shop_count(latitude, longitude, MAX_RADIUS)
                        #logger.debug('Thread ID: %s, Shop Counts Counts for line: %s = %s in 200m, %s in 1000m',
                        #             threadId,
                        #             line_count, count_shop_200m, count_shop_1000m)

                        #logger.debug('Thread ID: %s, Extracting Tourist Attraction Counts for line: %s', threadId,
                        #             line_count)
                        count_tourist_attractions_200m = get_tourist_attractions_count(latitude, longitude, MIN_RADIUS)
                        count_tourist_attractions_1000m = get_tourist_attractions_count(latitude, longitude, MAX_RADIUS)
                        #logger.debug('Thread ID: %s, Tourist Attraction Counts for line: %s = %s in 200m, %s in 1000m', threadId,
                        #             line_count, count_tourist_attractions_200m, count_tourist_attractions_1000m)

                        retries = MAX_RETRIES + MAX_RETRIES
                    except Exception:
                        print('Thread ID:', threadId, 'Exception occurred in extraction from Overpass API in trial attempt', retries)
                        # logger.info('Thread ID: %s, Exception occurred in extraction from Overpass API in trial attempt: %s', threadId, retries)
                        retries += 1
                        time.sleep(SLEEP_DURATION)
                     
                if retries == MAX_RETRIES + MAX_RETRIES:

                    new_data = [count_subway_200m, count_subway_1000m, count_bus_stop_200m, count_bus_stop_1000m,
                                count_restaurant_200m, count_restaurant_1000m,
                                # count_cafe_200m, count_cafe_1000m,
                                count_shop_200m, count_shop_1000m,
                                count_tourist_attractions_200m, count_tourist_attractions_1000m]
                else:

                    new_data = [VAL_IF_NOT_FOUND, VAL_IF_NOT_FOUND,
                                VAL_IF_NOT_FOUND, VAL_IF_NOT_FOUND,
                                VAL_IF_NOT_FOUND, VAL_IF_NOT_FOUND,
                                # VAL_IF_NOT_FOUND, VAL_IF_NOT_FOUND,
                                VAL_IF_NOT_FOUND, VAL_IF_NOT_FOUND,
                                VAL_IF_NOT_FOUND, VAL_IF_NOT_FOUND]

                print(line_count, ": Coordinates= ", latitude, ",", longitude, ". New data:", new_data)
                row.extend(new_data)
                proximity_df.loc[len(proximity_df)] = row

    # logger.info('Thread Completed for file: %s, Thread ID: %s, Output File: %s', input_file_name, threadId, output_file_name)
    proximity_df.to_csv(output_file_name, index=None)
    print('completed')
    return True

def pandasDFfromFile():
    '''
    Create smaller files from initial concatenated listings file
    '''
    subset_cols = ['id', 'latitude', 'longitude']
    df = pd.read_csv(os.path.join(DATA_SET_DIRECTORY, FILE_NAME_MISSING_FROM_ROUND1),
                     usecols=subset_cols)
    df_unique_id_coordinates = df.drop_duplicates(subset=['id', 'latitude', 'longitude'])
    data_set_size = int(df_unique_id_coordinates.size / len(subset_cols))
    print(data_set_size)
    for i in range(NUM_DATA_SETS):
        start_index = int(data_set_size / NUM_DATA_SETS) * i
        end_index = int(data_set_size / NUM_DATA_SETS) * (i + 1)
        if i == NUM_DATA_SETS - 1:
            df_small = df_unique_id_coordinates[start_index:]
        else:
            df_small = df_unique_id_coordinates[start_index:end_index]
        file_identifier = "{0}_{1}_to_{2}".format(i, start_index, end_index)
        logger.info('File id: %s ,Size: %s', file_identifier, int(df_small.size / NUM_DATA_SETS))
        df_small.to_csv(os.path.join(DATA_SET_DIRECTORY, FILE_NAME_MISSING_ID_COORDINATES.format(id=file_identifier)))


# print (readLatituteLongitude(os.path.join( DATA_SET_DIRECTORY, FILE_NAME )))
def threaded_location_extraction():
    input_path = os.path.join(DATA_SET_DIRECTORY, INPUT_FOLDER_NAME_UNIQUE_LISTINGS) # ./unique_listings
    file_names = os.listdir(input_path)
    
    # Remove Output Directory and Remove .DS_Store Directory
    files_to_remove = ['output', '.DS_Store']

    pool = ThreadPoolExecutor(NUM_THREADS)
    threads = []

    for _idx, file in enumerate(file_names[:NUM_THREADS]):
        thread = pool.submit(extractLocationFeatures, _idx, input_path + '/' + file)
        threads.append(thread)
        
    pool.shutdown(wait=True)

threaded_location_extraction()

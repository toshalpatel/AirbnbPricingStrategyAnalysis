import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import sys
import re
import pdb
from datetime import datetime
from io import StringIO

## Paths 
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_PATH, "airbnb_data")

airbnb_data_dir = os.path.join(DATA_PATH, "airbnb")
os.makedirs(airbnb_data_dir, exist_ok=True)
           
airbnb_download_urls_df_all_path = os.path.join(airbnb_data_dir, "airbnb_all_download_urls.csv")
airbnb_listings_full_path = os.path.join(airbnb_data_dir, "airbnb_listings_full.csv")
airbnb_listings_path = os.path.join(airbnb_data_dir, "airbnb_listings.csv")
airbnb_reviews_full_path = os.path.join(airbnb_data_dir, "airbnb_reviews_full.csv")
airbnb_reviews_path = os.path.join(airbnb_data_dir, "airbnb_reviews.csv")
airbnb_neighbourhoods_path = os.path.join(airbnb_data_dir, "airbnb_neighbourhoods.csv")
airbnb_calendar_path = os.path.join(airbnb_data_dir, "airbnb_calendar.csv")

airbnb_url_row = {}

airbnb_all_download_urls = pd.DataFrame(columns = ['file_name', 'year', 'month', 'day']) # airbnb_all_download_urls
airbnb_listings_full_df = pd.DataFrame(columns = ['id', 'listing_url', 'scrape_id', 'last_scraped', 'name','description', 'neighborhood_overview', 'picture_url', 'host_id', 'host_url', 'host_name', 'host_since', 'host_location', 'host_about' , 'host_response_time', 'host_response_rate', 'host_acceptance_rate', 'host_is_superhost', 'host_thumbnail_url', 'host_picture_url', 'host_neighbourhood','host_listings_count', 'host_total_listings_count', 'host_verifications', 'host_has_profile_pic', 'host_identity_verified', 'neighbourhood', 'neighbourhood_cleansed', 'neighbourhood_group_cleansed', 'latitude', 'longitude','property_type', 'room_type', 'accommodates', 'bathrooms', 'bathrooms_text', 'bedrooms', 'beds', 'amenities', 'price', 'minimum_nights','maximum_nights', 'minimum_minimum_nights', 'maximum_minimum_nights', 'minimum_maximum_nights', 'maximum_maximum_nights', 'minimum_nights_avg_ntm', 'maximum_nights_avg_ntm', 'calendar_updated', 'has_availability', 'availability_30','availability_60', 'availability_90', 'availability_365', 'calendar_last_scraped', 'number_of_reviews', 'number_of_reviews_ltm', 'number_of_reviews_l30d', 'first_review', 'last_review', 'review_scores_rating','review_scores_accuracy', 'review_scores_cleanliness', 'review_scores_checkin', 'review_scores_communication', 'review_scores_location', 'review_scores_value', 'license', 'instant_bookable', 'calculated_host_listings_count', 'calculated_host_listings_count_entire_homes', 'calculated_host_listings_count_private_rooms', 'calculated_host_listings_count_shared_rooms', 'reviews_per_month' ])  # listings.csv in listings.csv.gz
airbnb_reviews_full_df = pd.DataFrame(columns = ['listing_id', 'id', 'date', 'reviewer_id', 'reviewer_name','comments']) # reviews.csv in reviews.csv.gz																										
airbnb_listings_df = pd.DataFrame(columns = ['id', 'name', 'host_id', 'host_name', 'neighbourhood_group','neighbourhood', 'latitude', 'longitude', 'room_type', 'price','minimum_nights', 'number_of_reviews', 'last_review', 'reviews_per_month', 'calculated_host_listings_count','availability_365']) # listings.csv 
airbnb_reviews_df = pd.DataFrame(columns = ['listing_id', 'date']) # reviews.csv 	
airbnb_neighbourhoods_df = pd.DataFrame(columns = ['neighbourhood_group', 'neighbourhood']) # neighbourhoods.csv 
airbnb_calendar_df = pd.DataFrame(columns =['listing_id', 'date', 'available', 'price', 'adjusted_price','minimum_nights', 'maximum_nights']) # calendar.csv

## Starting URLs ##

COUNTRY_NAME = '/singapore' 
STATE_NAME = '/sg' 
CITY_NAME = '/singapore'

download_url = "http://data.insideairbnb.com" + COUNTRY_NAME + STATE_NAME + CITY_NAME
start_url = "http://insideairbnb.com/get-the-data.html"
  
r = requests.get(start_url,timeout=60)
r_html = r.text 

## Beautiful Soup is used for crawling the data
soup = BeautifulSoup(r_html, 'html.parser')

CITY_TAG = 'singapore'
CLASS_NAME = 'table table-hover table-striped ' + CITY_TAG
airbnb_archived = soup.find('table', {'class': CLASS_NAME })
airbnb_list = airbnb_archived.find_all('a')

listings_full_counter = 0
listings_counter = 0
reviews_full_counter = 0
reviews_counter = 0
neighbourhoods_counter = 0
calendar_counter = 0

## Start Crawling ##

for atag in airbnb_list:
    date = atag.get('href').split('/')[6].split('-') # date
    
    year = date[0]
    month = date[1]
    day = date[2]

    filename = atag.get('href').split('/')[-1] # filename e.g. csv
    
    airbnb_url_row['file_name'] = filename
    airbnb_url_row['year'] = year
    airbnb_url_row['month'] = month
    airbnb_url_row['day'] = day
    airbnb_url_row['csv_url'] = atag.get('href')
    


    if(airbnb_url_row['file_name'] == 'listings.csv.gz' and airbnb_url_row['year'] in ['2019','2020','2021']):
        airbnb_record_listings_full = pd.read_csv(airbnb_url_row['csv_url'], compression='gzip', error_bad_lines=False)
        airbnb_record_listings_full['scrapped_date'] = str(month)+'-' + str(year)
        airbnb_listings_full_df = airbnb_listings_full_df.append(airbnb_record_listings_full, ignore_index=True)
        airbnb_listings_full_df['scrapped_date'] = str(month)+'-' + str(year)
        listings_full_counter += 1
        print('listing.csv.gz', listings_full_counter)
        print(airbnb_url_row['year'])

## Uncomment the following elif statement for crawling listings.csv
#         elif(airbnb_url_row['file_name'] == 'listings.csv' and airbnb_url_row['year'] in ['2019','2020','2021']):
#             airbnb_record_listings = pd.read_csv(airbnb_url_row['csv_url'])
#             airbnb_listings_df = airbnb_listings_df.append(airbnb_record_listings, ignore_index=True)
#             listings_counter += 1
#             print('listing.csv', listings_counter)
#             print(airbnb_url_row['year'])

## Uncomment the following elif statement for crawling reviews.csv
#         elif(airbnb_url_row['file_name'] == 'reviews.csv' and airbnb_url_row['year'] in ['2019','2020','2021']):
#             airbnb_record_reviews = pd.read_csv(airbnb_url_row['csv_url'])
#             airbnb_reviews_df = airbnb_reviews_df.append(airbnb_record_reviews, ignore_index=True)
#             reviews_counter += 1
#             print('reviews.csv', reviews_counter)
#             print(airbnb_url_row['year'])

    elif(airbnb_url_row['file_name'] == 'reviews.csv.gz' and airbnb_url_row['year'] in ['2019','2020','2021']):
        airbnb_record_reviews_full = pd.read_csv(airbnb_url_row['csv_url'], compression='gzip', error_bad_lines=False)
        airbnb_record_reviews_full['scrapped_date'] = str(month)+'-' + str(year)
        airbnb_reviews_full_df = airbnb_reviews_full_df.append(airbnb_record_reviews_full, ignore_index=True)
        reviews_full_counter += 1
        print('reviews.csv.gz', reviews_full_counter)
        print(airbnb_url_row['year'])

## Uncomment the following elif statement for crawling neighbourhoods.csv
#         elif(airbnb_url_row['file_name'] == 'neighbourhoods.csv' and airbnb_url_row['year'] in ['2019','2020','2021']):
#             airbnb_record_neighbourhoods = pd.read_csv(airbnb_url_row['csv_url'])
#             airbnb_neighbourhoods_df = airbnb_neighbourhoods_df.append(airbnb_record_neighbourhoods, ignore_index=True)
#             neighbourhoods_counter += 1
#             print('neighbourhoods.csv', neighbourhoods_counter)
#             print(airbnb_url_row['year'])

    elif(airbnb_url_row['file_name'] == 'calendar.csv.gz' and airbnb_url_row['year'] in ['2019','2020','2021']):
        if(calendar_counter == 0):
            airbnb_record_calendar = pd.read_csv(airbnb_url_row['csv_url'])
            airbnb_record_calendar['scrapped_date'] = str(month) +'-' + str(year)
            airbnb_record_calendar.to_csv(airbnb_calendar_path, index=None)
            print('new')
            # airbnb_calendar_df = airbnb_calendar_df.append(airbnb_record_calendar, ignore_index=True)
        else:
            airbnb_record_calendar = pd.read_csv(airbnb_url_row['csv_url'])
            airbnb_record_calendar['scrapped_date'] = str(month) + '-' + str(year)
            airbnb_record_calendar.to_csv(airbnb_calendar_path, mode='a', header=False, index=None)
            print('append')
#             import pdb
#             pdb.set_trace()

        calendar_counter += 1
        print('calendar.csv.gz', calendar_counter)
        print(airbnb_url_row['year'])
    
    
    if(airbnb_url_row['year'] in ['2019','2020','2021']):
        airbnb_all_download_urls = airbnb_all_download_urls.append(airbnb_url_row, ignore_index=True)
    else:
        print(airbnb_url_row['year'])

## save to csv ##
        
airbnb_listings_full_df.to_csv(airbnb_listings_full_path, index=None)
# airbnb_listings_df.to_csv(airbnb_listings_path, index=None)

airbnb_reviews_full_df.to_csv(airbnb_reviews_full_path, index=None)
# airbnb_reviews_df.to_csv(airbnb_reviews_path, index=None)

# airbnb_neighbourhoods_df.to_csv(airbnb_neighbourhoods_path, index=None)
# airbnb_calendar_df.to_csv(airbnb_calendar_path, index=None)

airbnb_all_download_urls.to_csv(airbnb_download_urls_df_all_path, index=None)

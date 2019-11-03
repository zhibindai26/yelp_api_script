# -*- coding: utf-8 -*-

from __future__ import print_function
import math
import requests
import sys
import csv
from datetime import datetime
from urllib.error import HTTPError
from urllib.parse import quote
import configparser
import pandas as pd

# CONSTANTS
CONFIG_FILE = "config.ini"

RADIUS = 40000  # in meters
COUNTER = 1
OFFSET = 0

API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash

DF_COLUMNS = [
    'name',
    'url',
    'categories',
    'location',
    'rating',
    'review_count',
    'display_phone'
]

config = configparser.ConfigParser()
config.read(CONFIG_FILE)


class YelpFusion:
    # API constants, you shouldn't have to change these.

    def __init__(self, term, location, radius, offset):
        self.API_KEY = config.get('creds', 'api_key')
        self.term = term
        self.location = location
        self.radius = radius
        self.offset = offset

    def request(self, path, url_params=None):
        """Given your API_KEY, send a GET request to the API."""

        url_params = url_params or {}
        url = '{0}{1}'.format(API_HOST, quote(path.encode('utf8')))
        headers = {
            'Authorization': 'Bearer %s' % self.API_KEY,
        }

        print(u'Querying {0} ...'.format(url))

        response = requests.request('GET', url, headers=headers, params=url_params)

        return response.json()

    def search(self):
        """Query the Search API by a search term and location."""

        url_params = {
            'term': self.term.replace(' ', '+'),
            'location': self.location.replace(' ', '+'),
            'limit': 50,
            'radius': self.radius,
            'offset': self.offset
        }
        return self.request(SEARCH_PATH, url_params=url_params)

    def query_api_count(self):
        response = self.search()
        total_results = response.get('total')
        num_searches = int(math.ceil(total_results / 50.0))

        if num_searches < 20:
            return num_searches
        else:
            return 20

    def query_api(self):
        response = self.search()
        businesses = response.get('businesses')

        if not businesses:
            print(f'No businesses for {self.term} in {self.location} found.')
            return None

        business_data = self.__convert_to_df(businesses)

        self.__write_csv(business_data)

    def __convert_to_df(self, dict_to_convert):

        # convert response data to pandas DF
        df = pd.DataFrame.from_dict(dict_to_convert)

        # filter to get needed columns
        selected_cols = df[DF_COLUMNS]

        address_df = selected_cols.copy()

        # parse location data
        address_df['Address'] = address_df.loc[:, 'location'].apply(lambda x: x.get('display_address'))

        final_addr_df = address_df.copy()

        final_addr_df['Address1'] = final_addr_df.loc[:, 'Address'].apply(lambda x: self.__list_to_str(x))

        # remove redundant address cols
        final_df = final_addr_df.drop(['location', 'Address'], axis=1)

        return final_df

    @staticmethod
    def __list_to_str(ls):
        return " ".join(ls)

    def __write_csv(self, df):

        today = datetime.today().strftime('%m-%d-%Y')
        csv_file = self.term + '_' + self.location + '_' + today + '.csv'
        if self.offset == 0:
            df.to_csv(csv_file, mode='a', header=True, index=False)
        else:
            df.to_csv(csv_file, mode='a', header=False, index=False)


if __name__ == '__main__':
    search_term = config.get("search", "search_term")
    zip_code = config.get("search", "zip_code")

    try:
        count_search = YelpFusion(search_term, zip_code, RADIUS, 0)
        query_count = count_search.query_api_count()
        while COUNTER <= query_count:
            result_search = YelpFusion(search_term, zip_code, RADIUS, OFFSET)
            result_search.query_api()
            COUNTER += 1
            OFFSET += 50
    except HTTPError as error:
        sys.exit(
            'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                error.code,
                error.url,
                error.read(),
            )
        )

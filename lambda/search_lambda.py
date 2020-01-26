import math
import sys
import csv
from datetime import datetime
from urllib.parse import quote
import json
import pandas as pd
import requests

# CONSTANTS
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


class YelpFusion:
    # API constants, you shouldn't have to change these.

    def __init__(self, api_key, term, location, radius, offset):
        self.API_KEY = api_key
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

        return self.__parse_data(businesses)

    def __parse_data(self, dict_to_convert):

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

        return final_df.to_dict('records')

    @staticmethod
    def __list_to_str(ls):
        return " ".join(ls)


def get_yelp_results(event, context):
    search_term = event["query"]
    zip_code = event["zip"]
    api_key = event["yelp_key"]
    radius_input = int(event["radius"]) * 1609
    radius = radius_input if radius_input < 40000 else 40000 # miles ==> meters
    count = 1
    offset = 0

    results_list = []
    yelp_search = YelpFusion(api_key, search_term, zip_code, radius, offset)
    query_count = yelp_search.query_api_count()

    while count <= query_count:
        result_set = yelp_search.query_api()
        count += 1
        offset += 50
        for result in result_set:
            results_list.append(result)

    # body = json.dumps(results_list)

    response_obj = {}
    response_obj['statusCode'] = 200
    response_obj['body'] = results_list
    return response_obj
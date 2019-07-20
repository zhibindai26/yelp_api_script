# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import math
import requests
import sys
import csv
from datetime import datetime

# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
    import configparser
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode
    import ConfigParser

dir_name = os.path.dirname(__file__)
config_file = os.path.join(dir_name, "..\\config\\config.ini")
csv_folder = os.path.join(dir_name, "..\\csv\\")

config = ConfigParser.ConfigParser()
config.read(config_file)


class YelpFusion:
    # API constants, you shouldn't have to change these.
    API_HOST = 'https://api.yelp.com'
    SEARCH_PATH = '/v3/businesses/search'
    BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash

    def __init__(self, term, location, radius, offset):
        self.API_KEY = config.get('creds', 'api_key')
        self.term = term
        self.location = location
        self.radius = radius
        self.offset = offset

    def request(self, path, url_params=None):
        """Given your API_KEY, send a GET request to the API.

        Args:
            path (str): The path of the API after the domain.
            url_params (dict): An optional set of query parameters in the request.

        Returns:
            dict: The JSON response from the request.

        Raises:
            HTTPError: An error occurs from the HTTP request.
        """

        url_params = url_params or {}
        url = '{0}{1}'.format(self.API_HOST, quote(path.encode('utf8')))
        headers = {
            'Authorization': 'Bearer %s' % self.API_KEY,
        }

        print(u'Querying {0} ...'.format(url))

        response = requests.request('GET', url, headers=headers, params=url_params)

        return response.json()

    def search(self, ):
        """Query the Search API by a search term and location.

        Returns:
            dict: The JSON response from the request.
        """

        url_params = {
            'term': self.term.replace(' ', '+'),
            'location': self.location.replace(' ', '+'),
            'limit': 50,
            'radius': self.radius,
            'offset': self.offset
        }
        return self.request(self.SEARCH_PATH, url_params=url_params)

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
            print(u'No businesses for {0} in {1} found.'.format(self.term, self.location))
            return

        self.convert_to_list(businesses)

    def convert_to_list(self, dict_to_convert):
        final_list = []
        item_ls = []

        for item in dict_to_convert:
            item_ls.append(item['name'].encode('utf-8').strip())
            item_ls.append(item['categories'])
            item_ls.append(str(item['location']['address1']).encode('utf-8').strip())
            item_ls.append(str(item['location']['address2']).encode('utf-8').strip())
            item_ls.append(item['location']['city'].encode('utf-8').strip())
            item_ls.append(item['location']['state'].encode('utf-8').strip())
            item_ls.append(item['location']['zip_code'].encode('utf-8').strip())
            item_ls.append(item['display_phone'].encode('utf-8').strip())
            item_ls.append(item['rating'])
            item_ls.append(item['review_count'])
            item_ls.append(item['url'].encode('utf-8').strip())

            final_list.append(item_ls)
            item_ls = []

        self.write_csv(final_list)

    def write_csv(self, results_list):
        columns = [
            'name',
            'categories',
            'address 1',
            'address 2',
            'city',
            'state',
            'zip code',
            'phone #',
            'rating',
            '# of reviews',
            'url'
        ]
        columns = [x.upper() for x in columns]

        today = datetime.today().strftime('%m-%d-%Y')
        csv_file = self.term + '_' + self.location + '_' + today + '_results.csv'
        with open(csv_folder + csv_file, 'ab') as output:
            result_writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            if self.offset == 0:
                result_writer.writerow(columns)
            for item in results_list:
                result_writer.writerow(item)


def read_search_list(search_list):
    search_and_location = []

    with open(csv_folder + search_list + '.csv', 'r') as f:
        next(f)
        for line in f:
            line = line.strip()
            line = line.split("|")
            search_and_location.append([line[0], line[1]])

    return search_and_location


if __name__ == '__main__':
    radius = 40000  # in meters
    counter = 1
    offset = 0

    searches = read_search_list("med_spa")
    for search in searches:
        try:
            count_search = YelpFusion(search[0], search[1], radius, 0)
            query_count = count_search.query_api_count()
            while counter <= query_count:
                result_search = YelpFusion(search[0], search[1], radius, offset)
                result_search.query_api()
                counter += 1
                offset += 50
        except HTTPError as error:
            sys.exit(
                'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                    error.code,
                    error.url,
                    error.read(),
                )
            )

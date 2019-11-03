CONFIG_FILE = "config.ini"

RADIUS = 40000  # in meters
COUNTER = 1
OFFSET = 0

API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash

CSV_COLUMNS = [
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

DF_COLUMNS = [
    'name',
    'url',
    'categories',
    'location',
    'rating',
    'review_count',
    'display_phone'
]
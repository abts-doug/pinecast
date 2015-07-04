import json

import requests
from django.conf import settings


def query(collection, q):
    req = requests.get(
        'https://api.getconnect.io/events/%s' % collection,
        params={'query': json.dumps(q)},
        headers={'X-Project-Id': settings.GETCONNECT_IO_PID,
                 'X-Api-Key': settings.GETCONNECT_IO_QUERY_KEY})
    return req.json()


def total_listens(podcast):
    data = query('listen', {'select': {'episode': 'count'}})
    return data['results'][0]['episode']


def total_listens_this_week(podcast):
    data = query('listen', {'select': {'episode': 'count'}, 'timeframe': 'this_week'})
    return data['results'][0]['episode']


def total_subscribers(podcast):
    data = query('subscribe', {'select': {'podcast': 'count'}, 'timeframe': 'today'})
    return data['results'][0]['podcast']

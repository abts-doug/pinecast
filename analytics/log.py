import json

import requests
from django.conf import settings


def write(collection, blob):
    if 'profile' in blob and 'ip' in blob['profile']:
        blob['profile']['country'] = _get_country(blob['profile']['ip'])
    _post(collection, blob)


def _post(collection, payload):
    posted = requests.post(
        'https://api.getconnect.io/events/%s' % collection,
        data=json.dumps(payload),
        headers={'X-Project-Id': settings.GETCONNECT_IO_PID,
                 'X-Api-Key': settings.GETCONNECT_IO_PUSH_KEY})
    if posted.status_code != 200 and posted.status_code != 409:
        # 409 is a duplicate ID error, which is expected
        print posted.status_code, posted.text
    return posted

def _get_country(ip):
    if ip == '127.0.0.1':
        return 'US'
    res = requests.get('http://www.telize.com/geoip/%s' % ip)
    return res.json()['country_code']

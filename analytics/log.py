import requests
from django.conf.settings import GETCONNECT_IO_PID


def write(collection, blob):
    _post(collection, blob)


def _post(collection, payload):
    return requests.post(
        'https://api.getconnect.io/events/%s' % collection,
        data=payload,
        headers={'X-Project-Id': GETCONNECT_IO_PID,
                 'X-Api-Key': GETCONNECT_IO_PUSH_KEY})

import requests
from django.conf import settings


def write(collection, blob):
    _post(collection, blob)


def _post(collection, payload):
    return requests.post(
        'https://api.getconnect.io/events/%s' % collection,
        data=payload,
        headers={'X-Project-Id': settings.GETCONNECT_IO_PID,
                 'X-Api-Key': settings.GETCONNECT_IO_PUSH_KEY})

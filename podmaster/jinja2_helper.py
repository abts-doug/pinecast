import datetime
import json

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.urlresolvers import reverse
from jinja2 import Environment, evalcontextfilter


def environment(**options):
    options['autoescape'] = True
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'str': str,
        'url': reverse,
        'plural': plural,
    })
    env.filters['json'] = json.dumps
    env.filters['pretty_date'] = pretty_date
    return env


def plural(sing, plur, n, **kwargs):
    return (plur if n != 1 else sing).format(**kwargs)

def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.datetime.utcnow()
    if type(time) is int:
        diff = now - datetime.datetime.fromtimestamp(time)
    elif isinstance(time, datetime.datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return 'the future'

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return plural('{n} second ago', '{n} seconds ago', second_diff, n=str(second_diff))
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return plural('{n} minute ago', '{n} minutes ago', second_diff / 60, n=str(second_diff / 60))
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return plural('{n} hour ago', '{n} hour ago', second_diff / 3600, n=str(second_diff / 3600))
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return plural('{n} hour ago', '{n} hour ago', second_diff / 3600, n=str(second_diff / 3600))
        return str(day_diff) + " day(s) ago"
    if day_diff < 31:
        return str(day_diff / 7) + " week(s) ago"
    if day_diff < 365:
        return str(day_diff / 30) + " month(s) ago"
    return str(day_diff / 365) + " year(s) ago"

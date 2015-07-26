import datetime
import hashlib
import json

import gfm
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
        'gravatar': gravatar,
    })
    env.filters['https'] = lambda s: ('https:%s' % s[5:]) if s.startswith('http:') else s
    env.filters['json'] = json.dumps
    env.filters['markdown'] = gfm.markdown
    env.filters['pretty_date'] = pretty_date
    return env


def gravatar(s, size=40):
    dig = hashlib.md5(s).hexdigest()
    return 'https://www.gravatar.com/avatar/%s?s=%d' % (dig, size)

def plural(sing, plur, n, **kwargs):
    return (plur if n != 1 else sing).format(n=str(n), **kwargs)

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
            return plural('{n} second ago', '{n} seconds ago', second_diff)
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return plural('{n} minute ago', '{n} minutes ago', second_diff / 60)
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return plural('{n} hour ago', '{n} hours ago', second_diff / 3600)
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return plural('{n} day ago', '{n} days ago', day_diff)
    if day_diff < 31:
        return plural('{n} week ago', '{n} weeks ago', day_diff / 7)
    if day_diff < 365:
        return plural('{n} month ago', '{n} months ago', day_diff / 30)
    return plural('{n} year ago', '{n} years ago', day_diff / 365)

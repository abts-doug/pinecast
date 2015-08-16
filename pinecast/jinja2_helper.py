import datetime
import hashlib
import json

import bleach
import gfm
import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.translation import ugettext, ungettext
from jinja2 import Environment, evalcontextfilter

import accounts.payment_plans as payment_plans
import helpers
from accounts.models import UserSettings


def environment(**options):
    options['autoescape'] = True

    # Enable localization
    options.setdefault('extensions', [])
    if 'jinja2.ext.i18n' not in options['extensions']:
        options['extensions'].append('jinja2.ext.i18n')

    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'len': len,
        'str': str,
        'url': helpers.reverse,
        'plural': plural,  # DEPRECATED!
        'gravatar': gravatar,

        '_': ugettext,
        'gettext': ugettext,
        'ngettext': ungettext,
        'get_user_settings': UserSettings.get_from_user,
        'minimum_plan': minimum_plan,
        'PLAN_NAMES': payment_plans.PLANS_MAP,
        'PLANS': payment_plans.PLANS_RAW,
        'SUPPORT_URL': settings.SUPPORT_URL,
        'timezones': pytz.common_timezones,
        'tz_offset': helpers.tz_offset,
    })
    env.filters['https'] = lambda s: ('https:%s' % s[5:]) if s.startswith('http:') else s
    env.filters['json'] = json.dumps
    env.filters['markdown'] = gfm.markdown
    env.filters['pretty_date'] = pretty_date
    env.filters['sanitize'] = sanitize
    return env

def minimum_plan(user_settings, plan):
    if isinstance(user_settings, User):
        user_settings = UserSettings.get_from_user(user_settings)
    return payment_plans.minimum(user_settings.plan, plan)


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
        return ugettext('the future')

    if day_diff == 0:
        if second_diff < 10:
            return ugettext('just now')
        if second_diff < 60:
            return ungettext('{n} second ago', '{n} seconds ago', second_diff).format(n=second_diff)
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return ungettext('{n} minute ago', '{n} minutes ago', second_diff / 60).format(n=second_diff / 60)
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return ungettext('{n} hour ago', '{n} hours ago', second_diff / 3600).format(n=second_diff / 3600)
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return ungettext('{n} day ago', '{n} days ago', day_diff).format(n=day_diff)
    if day_diff < 31:
        return ungettext('{n} week ago', '{n} weeks ago', day_diff / 7).format(n=day_diff / 7)
    if day_diff < 365:
        return ungettext('{n} month ago', '{n} months ago', day_diff / 30).format(n=day_diff / 30)
    return ungettext('{n} year ago', '{n} years ago', day_diff / 365).format(n=day_diff / 365)


def sanitize(data):
    return bleach.clean(
        data,
        bleach.ALLOWED_TAGS + [
            'p', 'div', 'dl', 'dt', 'dd', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr'],
        {'*': ['src', 'href', 'title']}
    )

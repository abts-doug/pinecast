import datetime
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


def total_listens(podcast, episode_id=None):
    q = {'select': {'episode': 'count'},
         'filter': {'podcast': {'eq': unicode(podcast.id)}}}
    if episode_id:
        q['filter']['episode'] = {'eq': episode_id}
    data = query('listen', q)
    return data['results'][0]['episode'] + podcast.stats_base_listens


def total_listens_this_week(podcast):
    data = query(
        'listen',
        {'select': {'episode': 'count'},
         'timeframe': 'this_week',
         'filter': {'podcast': {'eq': unicode(podcast.id)}}})
    return data['results'][0]['episode']


def total_subscribers(podcast):
    data = query(
        'subscribe',
        {'select': {'podcast': 'count'},
         'timeframe': 'today',
         'filter': {'podcast': {'eq': unicode(podcast.id)}}})
    return data['results'][0]['podcast']


def get_top_episodes(podcast_id):
    data = query(
        'listen',
        {'select': {'podcast': 'count'},
         'groupBy': 'episode',
         'filter': {'podcast': {'eq': podcast_id}}})
    return data['results']



class Interval(object):
    def __init__(self, data):
        self.start = self._parse_date(data['interval']['start'])
        self.end = self._parse_date(data['interval']['end'])

        self.payload = data['results'][0] if data['results'] else {}

    def _parse_date(self, date):
        # 2015-07-06T00:00:00+00:00
        return datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S+00:00')

def process_intervals(intvs, interval_duration, label_maker, pick=None):
    if not intvs: return []

    processed = [Interval(x) for x in intvs]
    cursor = processed[0].start

    # Process the first interval early
    labels = [label_maker(cursor)]
    values = [processed.pop(0)]
    cursor += interval_duration

    if processed:
        while len(processed) and cursor <= processed[-1].start:
            labels.append(label_maker(cursor))
            values.append(processed.pop(0) if processed[0].start == cursor else None)
            cursor += interval_duration

    if pick:
        values = [(x.payload.get(pick, 0) if x else 0) for x in values]
    
    return {'labels': labels, 'dataset': values}


def process_groups(groups, label_mapping, label_key, pick=None):
    if not groups: return []

    labels = [label_mapping.get(x[label_key], x[label_key]) for x in groups]
    values = groups if not pick else [x[pick] for x in groups]

    return {'labels': labels, 'dataset': values}


def rotating_colors(sequence, key='color', highlight_key='highlight'):
    for x, c in zip(sequence, _colors_forever()):
        x[key] = c
        x[highlight_key] = _colorscale(c, 1.2)
        yield x


def _colors_forever():
    while 1:
        yield '#1abc9c'
        yield '#2ecc71'
        yield '#3498db'
        yield '#9b59b6'
        yield '#34495e'
        yield '#16a085'
        yield '#27ae60'
        yield '#2980b9'
        yield '#8e44ad'
        yield '#2c3e50'
        yield '#f1c40f'
        yield '#e67e22'
        yield '#e74c3c'
        yield '#f39c12'
        yield '#d35400'
        yield '#c0392b'


def _colorscale(hexstr, scalefactor):
    """
    Scales a hex string by ``scalefactor``. Returns scaled hex string.

    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.

    >>> colorscale("#DF3C3C", .5)
    #6F1E1E
    >>> colorscale("#52D24F", 1.6)
    #83FF7E
    >>> colorscale("#4F75D2", 1)
    #4F75D2
    """

    hexstr = hexstr.strip('#')

    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr

    r, g, b = int(hexstr[:2], 16), int(hexstr[2:4], 16), int(hexstr[4:], 16)

    r = max(0, min(r * scalefactor, 255))
    g = max(0, min(g * scalefactor, 255))
    b = max(0, min(b * scalefactor, 255))

    return "#%02x%02x%02x" % (r, g, b)

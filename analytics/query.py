import collections
import datetime
import json
import re

import grequests
import requests
from django.conf import settings


TIMZONE_KILLA = re.compile(r'(\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\d)[+\-]\d\d:\d\d')


def _query(collection, q, _handler):
    if 'timeframe' not in q and 'timezone' in q:
        del q['timezone']
    return _handler.get(
        'https://api.getconnect.io/events/%s' % collection,
        params={'query': json.dumps(q)},
        headers={'X-Project-Id': settings.GETCONNECT_IO_PID,
                 'X-Api-Key': settings.GETCONNECT_IO_QUERY_KEY})

def query(*args):
    return _query(*args, _handler=requests).json()

def query_async(*args):
    return _query(*args, _handler=grequests)

def query_async_resolve(async_queries):
    if isinstance(async_queries, list):
        return [x.json() for x in grequests.map(async_queries)]
    elif isinstance(async_queries, dict):
        items = async_queries.items()
        results = [x.json() for x in grequests.map([v for k, v in items])]
        return {k: results[i] for i, (k, v) in enumerate(items)}
    else:
        raise Exception('Unknown type passed to query_async_resolve')


def _query_async_switch(async):
    return query_async if async else query


class AsyncContext(object):
    def __init__(self):
        self.pending = []
        self.resolved = None

    def add(self, item, processor):
        self.pending.append(item)
        idx = len(self.pending) - 1

        return lambda: processor(self.resolve()[idx])

    def resolve(self):
        if self.resolved:
            return self.resolved
        self.resolved = [x.json() for x in grequests.map(self.pending)]
        return self.resolved


def total_listens(podcast, episode_id=None, async=False):
    q = {'select': {'episode': 'count'},
         'filter': {'podcast': {'eq': unicode(podcast.id)}}}
    if episode_id:
        q['filter']['episode'] = {'eq': episode_id}
    data = _query_async_switch(async)('listen', q)
    if not async:
        return data['results'][0]['episode'] + podcast.stats_base_listens
    else:
        return async.add(data, lambda d: d['results'][0]['episode'] + podcast.stats_base_listens)


def total_listens_this_week(podcast, async=False):
    data = _query_async_switch(async)(
        'listen',
        {'select': {'episode': 'count'},
         'timeframe': 'this_week',
         'filter': {'podcast': {'eq': unicode(podcast.id)}}})
    if not async:
        return data['results'][0]['episode']
    else:
        return async.add(data, lambda d: d['results'][0]['episode'])


def total_subscribers(podcast, async=False):
    data = _query_async_switch(async)(
        'subscribe',
        {'select': {'podcast': 'count'},
         'timeframe': 'today',
         'filter': {'podcast': {'eq': unicode(podcast.id)}}})
    if not async:
        return data['results'][0]['podcast']
    else:
        return async.add(data, lambda d: d['results'][0]['podcast'])


def get_top_episodes(podcast_id, async=False):
    data = _query_async_switch(async)(
        'listen',
        {'select': {'podcast': 'count'},
         'groupBy': 'episode',
         'filter': {'podcast': {'eq': podcast_id}}})
    if not async:
        return data['results']
    else:
        return async.add(data, lambda d: d['results'])



class Interval(object):
    def __init__(self, data):
        self.start = self._parse_date(data['interval']['start'])
        self.end = self._parse_date(data['interval']['end'])

        self.payload = data['results'][0] if data['results'] else {}

    def _parse_date(self, date):
        # We need to strip off the timezone because the times are always
        # returned in the correct timezone for the user. Python has issues
        # with parsing basically anything.

        # 2015-07-06T00:00:00+00:00
        stripped = TIMZONE_KILLA.match(date).group(1)
        # 2015-07-06T00:00:00
        return datetime.datetime.strptime(stripped, '%Y-%m-%dT%H:%M:%S')

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

def process_intervals_bulk(bulk_results, interval_duration, label_maker, pick=None):
    if not bulk_results: return [], []

    # print bulk_results
    processed = [[Interval(x) for x in results['results']] for results in bulk_results]
    cursor_start = min(x[0].start for x in processed if x)
    cursor_end = max(x[-1].end for x in processed if x)

    # Process the labels first
    label_cursor = cursor_start
    labels = []
    while label_cursor <= cursor_end:
        labels.append(label_maker(label_cursor))
        label_cursor += interval_duration

    datasets = []
    for results in processed:
        # If there are no results for this dataset, fille it with zeroed values
        if not results:
            datasets.append([0 for x in labels])
            continue

        values = []
        cursor = cursor_start
        # Set zeroed values for all data points before 
        while cursor <= cursor_end:
            if not results:
                values.append(0)
            elif results[0].start <= cursor <= results[-1].end:
                intv = results.pop(0)
                values.append(intv.payload.get(pick, 0))
            else:
                values.append(0)
            cursor += interval_duration

        datasets.append(values)

    return labels, datasets


def process_groups(groups, label_mapping=None, label_key=None, pick=None):
    if not groups: return []

    if not label_mapping: label_mapping = collections.defaultdict(collections.defaultdict)

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

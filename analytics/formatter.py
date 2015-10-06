import datetime

from django.utils.translation import ugettext

from . import query
from accounts.models import UserSettings


DELTAS = {
    'minutely': datetime.timedelta(minutes=1),
    'hourly': datetime.timedelta(hours=1),
    'daily': datetime.timedelta(days=1),
    'weekly': datetime.timedelta(weeks=1),
    'monthly': datetime.timedelta(weeks=4),
    'quarterly': datetime.timedelta(weeks=4 * 3),
    'yearly': datetime.timedelta(weeks=52),
}

USER_TIMEFRAMES = {
    'day': 'today',
    'yesterday': 'yesterday', # Should not be exposed in UI
    'month': {'previous': {'hours': 30 * 24}},
    'sixmonth': {'previous': {'hours': 6 * 30 * 24}},
    'year': {'previous': {'hours': 12 * 30 * 24}},
    'all': None,
}


class Format(object):
    def __init__(self, req, event_type):
        self.event_type = event_type
        self.req = req
        self.selection = {}
        self.criteria = {}
        self.timeframe = None
        self.interval_val = None
        self.group_by = None
        self.res = None

    def select(self, **kwargs):
        self.selection.update(kwargs)
        return self

    def where(self, **kwargs):
        self.criteria.update(kwargs)
        return self

    def group(self, by):
        self.group_by = by
        return self

    def during(self, timeframe=None, **kwargs):
        self.timeframe = timeframe or kwargs
        return self

    def last_thirty(self):
        self.timeframe = {'previous': {'hours': 30 * 24}}
        return self

    def interval(self, value=None):
        self.interval_val = value or self.req.GET.get('interval', 'daily')
        if self.interval_val not in DELTAS:
            self.interval_val = 'daily'
        return self

    def _process(self):
        assert self.selection
        q = {
            'select': self.selection,
            'timezone': UserSettings.get_from_user(self.req.user).tz_offset,
        }

        if self.criteria:
            q['filter'] = {k: {'eq': unicode(v)} for k, v in self.criteria.items()}
        if self.group_by:
            q['groupBy'] = self.group_by
        if self.timeframe:
            tf = USER_TIMEFRAMES[self.req.GET.get('timeframe', self.timeframe)]
            if tf:
                q['timeframe'] = tf
        if self.interval_val:
            q['interval'] = self.interval_val

        self.res = query.query(self.event_type, q)
        return self

    def format_country(self, label=None):
        if not self.res: self._process()

        key = self.selection.keys()[0]

        return [[ugettext('Country'), label or ugettext('Subscribers')]] + [
            [p[self.group_by], p[key]] for
            p in
            self.res['results'] if
            p[self.group_by]
        ]

    def format_intervals(self, label):
        if not self.interval_val: self.interval()
        if not self.res: self._process()

        key = self.selection.keys()[0]

        sformat = '%x %H:%M' if DELTAS[self.interval_val] < DELTAS['daily'] else '%x'
        out = query.process_intervals(
            self.res['results'],
            DELTAS[self.interval_val],
            lambda d: d.strftime(sformat),
            pick=key
        )

        if not out:
            out = {'dataset': [], 'labels': []}

        return {
            'labels': out['labels'],
            'datasets': [
                {'label': label,
                 'data': out['dataset'],
                 'fillColor': 'transparent',
                 'strokeColor': '#303F9F',
                 'pointColor': '#3F51B5',
                 'pointStrokeColor': '#fff'},
            ],
        }

    def format_breakdown(self, groups):
        if not self.res: self._process()

        key = self.selection.keys()[0]

        out = query.process_groups(
            self.res['results'],
            groups,
            self.group_by if isinstance(self.group_by, str) else self.group_by[0],
            pick=key
        )
        if not out:
            return []

        out = [{'label': unicode(label), 'value': value} for
                label, value in
                zip(out['labels'], out['dataset'])]

        return list(query.rotating_colors(out))

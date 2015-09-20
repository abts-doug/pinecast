import datetime

from django.utils.translation import ugettext

from . import query
from accounts.models import UserSettings


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
            q['timeframe'] = self.timeframe
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

        out = query.process_intervals(
            self.res['results'],
            datetime.timedelta(days=1), # TODO: Make this use the current interval
            lambda d: d.strftime('%x'),
            pick=key
        )

        if not out:
            out = {'data': [], 'labels': []}

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

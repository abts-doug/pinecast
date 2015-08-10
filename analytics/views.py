import datetime

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext, ugettext_lazy

import accounts.payment_plans as plans
from . import query
from accounts.models import Network, UserSettings
from dashboard.views import get_podcast
from pinecast.helpers import json_response
from podcasts.models import Podcast, PodcastEpisode


@login_required
@json_response(safe=False)
def podcast_subscriber_locations(req):
    pod = get_podcast(req, req.GET.get('podcast'))
    if not UserSettings.user_meets_plan(pod.owner, plans.PLAN_PRO):
        raise Http404()

    res = query.query(
        'subscribe',
        {'select': {'podcast': 'count'},
         'timeframe': 'yesterday',
         'groupBy': 'profile.country',
         'filter': {'podcast': {'eq': unicode(pod.id)}}})

    return [[ugettext('Country'), ugettext('Subscribers')]] + [
        [p['profile.country'], p['podcast']] for
        p in res['results'] if p['profile.country']
    ]


@login_required
@json_response(safe=False)
def podcast_listener_locations(req):
    pod = get_podcast(req, req.GET.get('podcast'))
    if not UserSettings.user_meets_plan(pod.owner, plans.PLAN_PRO):
        raise Http404()

    res = query.query(
        'listen',
        {'select': {'podcast': 'count'},
         'timeframe': 'this_month',
         'groupBy': 'profile.country',
         'filter': {'podcast': {'eq': unicode(pod.id)}},
         'timezone': UserSettings.get_from_user(req.user).tz_offset})

    return [[ugettext('Country'), ugettext('Subscribers')]] + [
        [p['profile.country'], p['podcast']] for
        p in res['results'] if p['profile.country']
    ]


@login_required
@json_response
def podcast_subscriber_history(req):
    pod = get_podcast(req, req.GET.get('podcast'))

    res = query.query(
        'subscribe',
        {'select': {'podcast': 'count'},
         'timeframe': 'this_month',
         'interval': 'daily',
         'filter': {'podcast': {'eq': unicode(pod.id)}},
         'timezone': UserSettings.get_from_user(req.user).tz_offset})

    out = query.process_intervals(
        res['results'],
        datetime.timedelta(days=1),
        lambda d: d.strftime('%x'),
        pick='podcast')

    return {'labels': out['labels'],
            'datasets': [
                {'label': pod.name,
                 'data': out['dataset'],
                 'fillColor': 'transparent',
                 'strokeColor': '#2980b9',
                 'pointColor': '#3498db',
                 'pointStrokeColor': '#fff'}
            ]}


@login_required
@json_response
def podcast_listen_history(req):
    pod = get_podcast(req, req.GET.get('podcast'))

    res = query.query(
        'listen',
        {'select': {'podcast': 'count'},
         'timeframe': 'this_month',
         'interval': 'daily',
         'filter': {'podcast': {'eq': unicode(pod.id)}},
         'timezone': UserSettings.get_from_user(req.user).tz_offset})

    out = query.process_intervals(
        res['results'],
        datetime.timedelta(days=1),
        lambda d: d.strftime('%x'),
        pick='podcast')

    if not out:
        return {'labels': [],
            'datasets': [
                {'label': pod.name,
                 'data': [],
                 'fillColor': 'transparent',
                 'strokeColor': '#2980b9',
                 'pointColor': '#3498db',
                 'pointStrokeColor': '#fff'}
            ]}

    return {'labels': out['labels'],
            'datasets': [
                {'label': pod.name,
                 'data': out['dataset'],
                 'fillColor': 'transparent',
                 'strokeColor': '#2980b9',
                 'pointColor': '#3498db',
                 'pointStrokeColor': '#fff'}
            ]}


@login_required
@json_response
def episode_listen_history(req):
    pod = get_podcast(req, req.GET.get('podcast'))
    ep = get_object_or_404(PodcastEpisode, podcast=pod, id=req.GET.get('episode'))

    res = query.query(
        'listen',
        {'select': {'episode': 'count'},
         'timeframe': 'this_month',
         'interval': 'daily',
         'filter': {'episode': {'eq': unicode(ep.id)}},
         'timezone': UserSettings.get_from_user(req.user).tz_offset})

    out = query.process_intervals(
        res['results'],
        datetime.timedelta(days=1),
        lambda d: d.strftime('%x'),
        pick='episode')

    if not out:
        return {'labels': [],
            'datasets': [
                {'label': ep.title,
                 'data': [],
                 'fillColor': 'transparent',
                 'strokeColor': '#2980b9',
                 'pointColor': '#3498db',
                 'pointStrokeColor': '#fff'}
            ]}

    return {'labels': out['labels'],
            'datasets': [
                {'label': ep.title,
                 'data': out['dataset'],
                 'fillColor': 'transparent',
                 'strokeColor': '#2980b9',
                 'pointColor': '#3498db',
                 'pointStrokeColor': '#fff'}
            ]}


SOURCE_MAP = {
    'direct': ugettext_lazy('Direct'),
    'rss': ugettext_lazy('Subscription'),
    'embed': ugettext_lazy('Embedded Player'),
    None: ugettext_lazy('Unknown'),
}

@login_required
@json_response(safe=False)
def podcast_listen_breakdown(req):
    pod = get_podcast(req, req.GET.get('podcast'))

    res = query.query(
        'listen',
        {'select': {'podcast': 'count'},
         'groupBy': 'source',
         'timeframe': 'this_month',
         'filter': {'podcast': {'eq': unicode(pod.id)}},
         'timezone': UserSettings.get_from_user(req.user).tz_offset})

    out = query.process_groups(
        res['results'],
        SOURCE_MAP,
        'source',
        pick='podcast')

    if not out:
        return []

    out = [{'label': unicode(label), 'value': value} for
            label, value in
            zip(out['labels'], out['dataset'])]

    return list(query.rotating_colors(out))

@login_required
@json_response(safe=False)
def podcast_listen_platform_breakdown(req):
    pod = get_podcast(req, req.GET.get('podcast'))
    if not UserSettings.user_meets_plan(pod.owner, plans.PLAN_STARTER):
        raise Http404()

    breakdown_type = req.GET.get('breakdown_type', 'device')
    if breakdown_type not in ['device', 'browser', 'os']: raise Http404()

    key = 'profile.%s' % breakdown_type

    res = query.query(
        'listen',
        {'select': {'podcast': 'count'},
         'groupBy': [key],
         'timeframe': 'this_month',
         'filter': {'podcast': {'eq': unicode(pod.id)}},
         'timezone': UserSettings.get_from_user(req.user).tz_offset})

    out = query.process_groups(
        res['results'],
        None,
        key,
        pick='podcast')

    if not out:
        return []

    out = [{'label': unicode(label), 'value': value} for
            label, value in
            zip(out['labels'], out['dataset'])]

    return list(query.rotating_colors(out))


@login_required
@json_response(safe=False)
def episode_listen_breakdown(req):
    pod = get_podcast(req, req.GET.get('podcast'))
    if not UserSettings.user_meets_plan(pod.owner, plans.PLAN_PRO):
        raise Http404()

    ep = get_object_or_404(PodcastEpisode, podcast=pod, id=req.GET.get('episode'))

    res = query.query(
        'listen',
        {'select': {'episode': 'count'},
         'groupBy': 'source',
         'filter': {'episode': {'eq': unicode(ep.id)}},
         'timezone': UserSettings.get_from_user(req.user).tz_offset})

    out = query.process_groups(
        res['results'],
        SOURCE_MAP,
        'source',
        pick='episode')

    if not out:
        return []

    out = [{'label': unicode(label), 'value': value} for
            label, value in
            zip(out['labels'], out['dataset'])]

    return list(query.rotating_colors(out))


@login_required
@json_response
def network_listen_history(req):
    net = get_object_or_404(Network, id=req.GET.get('network_id'), members__in=[req.user])

    pods = net.podcast_set.all()
    async_queries = []
    for pod in pods:
        res = query.query_async(
            'listen',
            {'select': {'podcast': 'count'},
             'timeframe': 'this_month',
             'interval': 'daily',
             'filter': {'podcast': {'eq': unicode(pod.id)}},
             'timezone': UserSettings.get_from_user(req.user).tz_offset})
        async_queries.append(res)

    query_results = query.query_async_resolve(async_queries)

    labels, datasets = query.process_intervals_bulk(
        query_results,
        datetime.timedelta(days=1),
        lambda d: d.strftime('%x'),
        pick='podcast'
    )

    formatted_datasets = []
    for i, dataset in enumerate(datasets):
        pod = pods[i]
        formatted_datasets.append({
            'label': pod.name,
            'data': dataset,
            'fillColor': 'transparent',
            'strokeColor': '#2980b9',
            'pointColor': '#3498db',
            'pointStrokeColor': '#fff',
        })

    return {
        'labels': labels,
        'datasets': list(
            query.rotating_colors(formatted_datasets,
                                  key='strokeColor',
                                  highlight_key='pointColor')
        ),
    }

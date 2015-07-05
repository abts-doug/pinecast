import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from . import query
from podcasts.models import Podcast, PodcastEpisode


def json_response(*args, **jr_kwargs):
    def wrapper(view):
        def func(*args, **kwargs):
            resp = view(*args, **kwargs)
            return JsonResponse(resp, safe=jr_kwargs.get('safe', True))
        return func
    if not jr_kwargs: return wrapper(*args)
    return wrapper


@login_required
@json_response(safe=False)
def podcast_subscriber_locations(req):
    pod = get_object_or_404(Podcast, slug=req.GET.get('podcast'), owner=req.user)

    res = query.query(
        'subscribe',
        {'select': {'podcast': 'count'},
         'timeframe': 'yesterday',
         'groupBy': 'profile.country',
         'filter': {'podcast': {'eq': unicode(pod.id)}}})

    return [['Country', 'Subscribers']] + [
        [p['profile.country'], p['podcast']] for
        p in
        res['results'] if
        p['profile.country']
    ]


@login_required
@json_response(safe=False)
def podcast_listener_locations(req):
    pod = get_object_or_404(Podcast, slug=req.GET.get('podcast'), owner=req.user)

    res = query.query(
        'listen',
        {'select': {'podcast': 'count'},
         'timeframe': 'this_month',
         'groupBy': 'profile.country',
         'filter': {'podcast': {'eq': unicode(pod.id)}}})

    return [['Country', 'Subscribers']] + [
        [p['profile.country'], p['podcast']] for
        p in
        res['results'] if
        p['profile.country']
    ]


@login_required
@json_response
def podcast_subscriber_history(req):
    pod = get_object_or_404(Podcast, slug=req.GET.get('podcast'), owner=req.user)

    res = query.query(
        'subscribe',
        {'select': {'podcast': 'count'},
         'timeframe': 'this_month',
         'interval': 'daily',
         'filter': {'podcast': {'eq': unicode(pod.id)}}})

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
    pod = get_object_or_404(Podcast, slug=req.GET.get('podcast'), owner=req.user)

    res = query.query(
        'listen',
        {'select': {'podcast': 'count'},
         'timeframe': 'this_month',
         'interval': 'daily',
         'filter': {'podcast': {'eq': unicode(pod.id)}}})

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
def episode_listen_history(req):
    pod = get_object_or_404(Podcast, slug=req.GET.get('podcast'), owner=req.user)
    ep = get_object_or_404(PodcastEpisode, podcast=pod, id=req.GET.get('episode'))

    res = query.query(
        'listen',
        {'select': {'episode': 'count'},
         'timeframe': 'this_month',
         'interval': 'daily',
         'filter': {'episode': {'eq': unicode(ep.id)}}})

    out = query.process_intervals(
        res['results'],
        datetime.timedelta(days=1),
        lambda d: d.strftime('%x'),
        pick='episode')

    return {'labels': out['labels'],
            'datasets': [{'label': ep.title, 'data': out['dataset']}]}


SOURCE_MAP = {
    'direct': 'Direct',
    'rss': 'Subscription',
    'embed': 'Embedded Player',
    None: 'Unknown',
}

@login_required
@json_response(safe=False)
def podcast_listen_breakdown(req):
    pod = get_object_or_404(Podcast, slug=req.GET.get('podcast'), owner=req.user)

    res = query.query(
        'listen',
        {'select': {'podcast': 'count'},
         'groupBy': 'source',
         'timeframe': 'this_month',
         'filter': {'podcast': {'eq': unicode(pod.id)}}})

    out = query.process_groups(
        res['results'],
        SOURCE_MAP,
        'source',
        pick='podcast')

    out = [{'label': label, 'value': value} for
            label, value in
            zip(out['labels'], out['dataset'])]

    return list(query.rotating_colors(out))


@login_required
@json_response(safe=False)
def episode_listen_breakdown(req):
    pod = get_object_or_404(Podcast, slug=req.GET.get('podcast'), owner=req.user)
    ep = get_object_or_404(PodcastEpisode, podcast=pod, id=req.GET.get('episode'))

    res = query.query(
        'listen',
        {'select': {'episode': 'count'},
         'groupBy': 'source',
         'filter': {'episode': {'eq': unicode(ep.id)}}})

    out = query.process_groups(
        res['results'],
        SOURCE_MAP,
        'source',
        pick='episode')

    out = [{'label': label, 'value': value} for
            label, value in
            zip(out['labels'], out['dataset'])]

    return list(query.rotating_colors(out))

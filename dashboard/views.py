import base64
import collections
import datetime
import hashlib
import hmac
import json
import time
import urllib
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

import analytics.query as analytics_query
from podcasts.models import CATEGORIES, Podcast, PodcastCategory, PodcastEpisode


def _pmrender(req, template, data=None):
    data = data or {}

    class DefaultEmptyDict(collections.defaultdict):
        def __init__(self):
            super(DefaultEmptyDict, self).__init__(lambda: '')

        def get(self, _, d=''):
            return d

    data.setdefault('default', DefaultEmptyDict())
    if not req.user.is_anonymous():
        data.setdefault('user', req.user)
        data.setdefault('podcasts', req.user.podcast_set.all())
        user_avatar = hashlib.md5(req.user.email).hexdigest()
        data.setdefault('user_avatar', 'http://www.gravatar.com/avatar/%s?s=40' % user_avatar)
    return render(req, template, data)

def json_response(view):
    def func(*args, **kwargs):
        resp = view(*args, **kwargs)
        return JsonResponse(resp)
    return func


@login_required
def dashboard(req):
    return _pmrender(req, 'dashboard.html')


@login_required
def podcast_dashboard(req, podcast_slug):
    pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)
    data = {
        'podcast': pod,
        'episodes': pod.podcastepisode_set.order_by('-publish'),
        'analytics': {
            'total_listens': analytics_query.total_listens(pod),
            'total_listens_this_week': analytics_query.total_listens_this_week(pod),
            'subscribers': analytics_query.total_subscribers(pod),
        },
    }
    return _pmrender(req, 'dashboard/podcast.html', data)


@login_required
def podcast_geochart(req, podcast_slug):
    pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)
    return _pmrender(req, 'dashboard/podcast_geochart.html', {'podcast': pod})


@login_required
def podcast_top_episodes(req, podcast_slug):
    pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)

    top_ep_data = analytics_query.get_top_episodes(unicode(pod.id))
    ep_ids = [x['episode'] for x in top_ep_data]
    episodes = PodcastEpisode.objects.filter(id__in=ep_ids)
    mapped = {unicode(ep.id): ep for ep in episodes}

    # This step is necessary to filter out deleted episodes
    top_ep_data = [x for x in top_ep_data if x['episode'] in mapped]

    # Sort the top episode data descending
    top_ep_data = reversed(sorted(top_ep_data, key=lambda x: x['podcast']))

    data = {
        'podcast': pod,
        'episodes': mapped,
        'top_ep_data': top_ep_data,
    }
    return _pmrender(req, 'dashboard/podcast_top_episodes.html', data)


@login_required
def new_podcast(req):
    ctx = {'PODCAST_CATEGORIES': json.dumps(list(CATEGORIES))}

    if not req.POST:
        return _pmrender(req, 'dashboard/new_podcast.html', ctx)

    try:
        pod = Podcast(
            slug=req.POST.get('slug'),
            name=req.POST.get('name'),
            subtitle=req.POST.get('subtitle'),
            cover_image=req.POST.get('image-url'),
            description=req.POST.get('description'),
            is_explicit=req.POST.get('is_explicit', 'false') == 'true',
            homepage=req.POST.get('homepage'),
            language=req.POST.get('language'),
            copyright=req.POST.get('copyright'),
            author_name=req.POST.get('author_name'),
            owner=req.user)
        pod.save()
        # TODO: The following line can throw an exception and create a
        # duplicate podcast if something has gone really wrong
        pod.set_category_list(req.POST.get('categories'))
    except Exception as e:
        print e
        ctx.update(default=req.POST, error=True)
        return _pmrender(req, 'dashboard/new_podcast.html', ctx)
    return redirect('podcast_dashboard', podcast_slug=pod.slug)


@login_required
def edit_podcast(req, podcast_slug):
    pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)

    ctx = {'podcast': pod,
           'PODCAST_CATEGORIES': json.dumps(list(CATEGORIES))}

    if not req.POST:
        return _pmrender(req, 'dashboard/edit_podcast.html', ctx)

    try:
        pod.slug = req.POST.get('slug')
        pod.name = req.POST.get('name')
        pod.subtitle = req.POST.get('subtitle')
        pod.description = req.POST.get('description')
        pod.is_explicit = req.POST.get('is_explicit', 'false') == 'true'
        pod.homepage = req.POST.get('homepage')
        pod.language = req.POST.get('language')
        pod.copyright = req.POST.get('copyright')
        pod.author_name = req.POST.get('author_name')
        pod.cover_image = req.POST.get('image-url')
        pod.set_category_list(req.POST.get('categories'))
        pod.save()
    except Exception as e:
        ctx.update(default=req.POST, error=True)
        return _pmrender(req, 'dashboard/edit_podcast.html', ctx)
    return redirect('podcast_dashboard', podcast_slug=pod.slug)


@login_required
def delete_podcast(req, podcast_slug):
    pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)
    if not req.POST:
        return _pmrender(req, 'dashboard/delete_podcast.html', {'podcast': pod})

    if req.POST.get('slug') != pod.slug:
        return redirect('dashboard')

    pod.delete()
    return redirect('dashboard')

@login_required
def delete_podcast_episode(req, podcast_slug, episode_id):
    pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)
    ep = get_object_or_404(PodcastEpisode, podcast=pod, id=episode_id)
    if not req.POST:
        return _pmrender(req, 'dashboard/delete_episode.html', {'podcast': pod, 'episode': ep})

    ep.delete()
    return redirect('podcast_dashboard', podcast_slug=pod.slug)


@login_required
def podcast_new_ep(req, podcast_slug):
    pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)

    if not req.POST:
        return _pmrender(req, 'dashboard/new_episode.html', {'podcast': pod})

    try:
        ep = PodcastEpisode(
            podcast=pod,
            title=req.POST.get('title'),
            subtitle=req.POST.get('subtitle'),
            publish=datetime.datetime.strptime(req.POST.get('publish'), '%Y-%m-%dT%H:%M'), # 2015-07-09T12:00
            description=req.POST.get('description'),
            duration=int(req.POST.get('duration-hours')) * 3600 + int(req.POST.get('duration-minutes')) * 60 + int(req.POST.get('duration-seconds')),

            audio_url=req.POST.get('audio-url'),
            audio_size=int(req.POST.get('audio-url-size')),
            audio_type=req.POST.get('audio-url-type'),

            image_url=req.POST.get('image-url'),

            copyright=req.POST.get('copyright'),
            license=req.POST.get('license'))
        ep.save()
    except Exception as e:
        return  _pmrender(req, 'dashboard/new_episode.html', {'podcast': pod, 'default': req.POST, 'error': True})
    return redirect('podcast_dashboard', podcast_slug=pod.slug)


@login_required
def edit_podcast_episode(req, podcast_slug, episode_id):
    pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)
    ep = get_object_or_404(PodcastEpisode, id=episode_id, podcast=pod)

    if not req.POST:
        return _pmrender(req, 'dashboard/edit_episode.html', {'podcast': pod, 'episode': ep})

    try:
        ep.title = req.POST.get('title')
        ep.subtitle = req.POST.get('subtitle')
        ep.publish = datetime.datetime.strptime(req.POST.get('publish'), '%Y-%m-%dT%H:%M') # 2015-07-09T12:00
        ep.description = req.POST.get('description')
        ep.duration = int(req.POST.get('duration-hours')) * 3600 + int(req.POST.get('duration-minutes')) * 60 + int(req.POST.get('duration-seconds'))

        ep.audio_url = req.POST.get('audio-url')
        ep.audio_size = int(req.POST.get('audio-url-size'))
        ep.audio_type = req.POST.get('audio-url-type')

        ep.image_url = req.POST.get('image-url')

        ep.copyright = req.POST.get('copyright')
        ep.license = req.POST.get('license')
        ep.save()
    except Exception as e:
        return  _pmrender(req, 'dashboard/new_episode.html', {'podcast': pod, 'episode': ep, 'default': req.POST, 'error': True})
    return redirect('podcast_episode', podcast_slug=pod.slug, episode_id=str(ep.id))


@login_required
def podcast_episode(req, podcast_slug, episode_id):
    pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)
    ep = get_object_or_404(PodcastEpisode, id=episode_id, podcast=pod)

    data = {
        'podcast': pod,
        'episode': ep,
        'analytics': {
            'total_listens': analytics_query.total_listens(pod, str(ep.id)),
        },
    }
    return _pmrender(req, 'dashboard/podcast_episode.html', data)


@login_required
@json_response
def slug_available(req):
    try:
        Podcast.objects.get(slug=req.GET.get('slug'))
        return {'valid': False}
    except Podcast.DoesNotExist:
        return {'valid': True}


@login_required
@json_response
def get_upload_url(req, podcast_slug, type):
    if type not in ['audio', 'image']:
        return Http404('Type not recognized')

    # TODO: Add validation around the 'type' and 'name' GET params

    if podcast_slug != '$none':
        pod = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)
        basepath = 'podcasts/%s/%s/' % (pod.id, type)
    else:
        basepath = 'podcasts/covers/'

    uid = str(uuid.uuid4())
    path = '%s%s/%s' % (basepath, uid, req.GET.get('name'))
    encoded_path = '%s%s/%s' % (basepath, uid, urllib.pathname2url(req.GET.get('name')))

    mime_type = req.GET.get('type')

    expires = int(time.time() + 60 * 60 * 24)
    amz_headers = 'x-amz-acl:public-read'

    string_to_sign = "PUT\n\n%s\n%d\n%s\n/%s/%s" % (mime_type, expires, amz_headers, settings.S3_BUCKET, encoded_path)
    print string_to_sign
    signature = base64.encodestring(hmac.new(settings.S3_SECRET_KEY.encode(), string_to_sign.encode('utf8'), hashlib.sha1).digest())
    signature = urllib.quote_plus(signature.strip())

    destination_url = 'http://%s.s3.amazonaws.com/%s' % (settings.S3_BUCKET, path)
    return {
        'url': '%s?AWSAccessKeyId=%s&Expires=%s&Signature=%s' % (destination_url, settings.S3_ACCESS_ID, expires, signature),
        'headers': {
            'x-amz-acl': 'public-read',
        },
        'destination_url': destination_url,
    }

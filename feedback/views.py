from django.shortcuts import get_object_or_404, render

import analytics.analyze as analyze
import analytics.log as analytics_log
from .models import Feedback
from dashboard.views import _pmrender
from podcasts.models import Podcast, PodcastEpisode


def podcast_comment_box(req, podcast_slug):
    pod = get_object_or_404(Podcast, slug=podcast_slug)
    if not req.POST:
        return _pmrender(req, 'feedback/comment_podcast.html', {'podcast': pod})

    try:
        ip = analyze.get_request_ip(req)
        f = Feedback(
            podcast=pod,
            sender=req.POST.get('email'),
            message=req.POST.get('message'),
            sender_ip=ip
        )
        f.save()
        analytics_log.write('feedback', {
            'podcast': unicode(pod.id),
            'episode': None,
            'profile': {
                'email': req.POST.get('email'),
                'email_host': req.POST.get('email').split('@')[1],
                'ip': ip,
                'ua': req.META.get('HTTP_USER_AGENT'),
            },
        }, req=req)
    except Exception:
        return _pmrender(req, 'feedback/comment_podcast.html',
                         {'podcast': pod, 'error': True, 'default': req.POST})

    return _pmrender(req, 'feedback/thanks.html', {'podcast': pod})


def ep_comment_box(req, podcast_slug, episode_id):
    pod = get_object_or_404(Podcast, slug=podcast_slug)
    ep = get_object_or_404(PodcastEpisode, podcast=pod, id=episode_id)
    if not req.POST:
        return _pmrender(req, 'feedback/comment_episode.html', {'podcast': pod, 'episode': ep})

    try:
        ip = analyze.get_request_ip(req)
        f = Feedback(
            podcast=pod,
            episode=ep,
            sender=req.POST.get('email'),
            message=req.POST.get('message'),
            sender_ip=ip
        )
        f.save()
        analytics_log.write('feedback', {
            'podcast': unicode(pod.id),
            'episode': unicode(ep.id),
            'profile': {
                'email': req.POST.get('email'),
                'email_host': req.POST.get('email').split('@')[1],
                'ip': ip,
                'ua': req.META.get('HTTP_USER_AGENT'),
            },
        }, req=req)
    except Exception:
        return _pmrender(req, 'feedback/comment_episode.html',
                         {'podcast': pod, 'episode': ep, 'error': True, 'default': req.POST})

    return _pmrender(req, 'feedback/thanks.html', {'podcast': pod})

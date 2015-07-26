from django.shortcuts import get_object_or_404, render

from .models import Feedback
from dashboard.views import _pmrender
from podcasts.models import Podcast, PodcastEpisode


def podcast_comment_box(req, podcast_slug):
    pod = get_object_or_404(Podcast, slug=podcast_slug)
    if not req.POST:
        return _pmrender(req, 'feedback/comment_podcast.html', {'podcast': pod})

    try:
        f = Feedback(
            podcast=pod,
            sender=req.POST.get('email'),
            message=req.POST.get('message')
        )
        f.save()
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
        f = Feedback(
            podcast=pod,
            episode=ep,
            sender=req.POST.get('email'),
            message=req.POST.get('message')
        )
        f.save()
    except Exception:
        return _pmrender(req, 'feedback/comment_episode.html',
                         {'podcast': pod, 'episode': ep, 'error': True, 'default': req.POST})

    return _pmrender(req, 'feedback/thanks.html', {'podcast': pod})

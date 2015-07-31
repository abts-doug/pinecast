from django.shortcuts import get_object_or_404, render

from . import models


def _srender(req, site, template, data=None):
    data = data or {}
    data.setdefault('site', site)
    return render(req, 'sites/%s/%s' % (site.theme, template), data)


def site_home(req, site_slug):
    site = get_object_or_404(models.Site, slug=site_slug)
    return _srender(req, site, 'home.html')

def site_episode(req, site_slug, episode_id):
    site = get_object_or_404(models.Site, slug=site_slug)
    return _srender(req, site, 'episode.html')

def site_post(req, site_slug, post_slug):
    site = get_object_or_404(models.Site, slug=site_slug)
    return _srender(req, site, 'post.html')

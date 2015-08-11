from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render

from . import models


def _srender(req, site, template, data=None):
    data = data or {}
    data.setdefault('site', site)
    return render(req, 'sites/%s/%s' % (site.theme, template), data)


def site_home(req, site_slug):
    site = get_object_or_404(models.Site, slug=site_slug)
    episodes = site.podcast.podcastepisode_set.all().order_by('-publish')
    paginator = Paginator(episodes, 5)
    try:
        pager = paginator.page(req.GET.get('page'))
    except PageNotAnInteger:
        pager = paginator.page(1)
    except EmptyPage:
        return redirect('site_home', site_slug=site_slug)
    return _srender(req, site, 'home.html', {'pager': pager})


def site_blog(req, site_slug):
    site = get_object_or_404(models.Site, slug=site_slug)
    posts = site.siteblogpost_set.all().order_by('-publish')
    paginator = Paginator(posts, 5)
    try:
        pager = paginator.page(req.GET.get('page'))
    except PageNotAnInteger:
        pager = paginator.page(1)
    except EmptyPage:
        return redirect('site_home', site_slug=site_slug)
    return _srender(req, site, 'blog.html', {'pager': pager})

def site_post(req, site_slug, post_slug):
    site = get_object_or_404(models.Site, slug=site_slug)
    post = get_object_or_404(models.SiteBlogPost, site=site, slug=post_slug)
    return _srender(req, site, 'post.html', {'post': post})

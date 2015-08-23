from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts import payment_plans
from accounts.models import Network, UserSettings
from sites.models import Site, SiteLink
from views import _pmrender, get_podcast, signer


def get_site(req, site_slug):
    site = get_object_or_404(Site, slug=site_slug)
    pod = site.podcast
    if (pod.owner != req.user and
        not Network.objects.filter(
            deactivated=False, members__in=[req.user], podcast__in=[pod]).count()):
        raise Http404()
    return site

@login_required
def new_site(req, podcast_slug):
    pod = get_podcast(req, podcast_slug)

    if not payment_plans.minimum(
        UserSettings.get_from_user(pod.owner).plan,
        payment_plans.FEATURE_MIN_SITES):
        raise Http404()

    data = {
        'podcast': pod,
        'themes': Site.SITE_THEMES,
    }

    if not req.POST:
        return _pmrender(req, 'dashboard/sites/page_new.html', data)

    try:
        site = Site(
            podcast=pod,
            slug=req.POST.get('slug'),
            theme=req.POST.get('theme'),
            cover_image_url=signer.unsign(req.POST.get('cover-url')) if req.POST.get('cover-url') else None,
            logo_url=signer.unsign(req.POST.get('logo-url')) if req.POST.get('logo-url') else None,
            analytics_id=req.POST.get('analytics_id')
        )
        site.save()
    except Exception as e:
        print e
        data.update(error=True, default=req.POST)
        return _pmrender(req, 'dashboard/sites/page_new.html', data)
    else:
        return redirect('site_options', site_slug=site.slug)


@login_required
def site_options(req, site_slug):
    site = get_site(req, site_slug)
    return _pmrender(req, 'dashboard/sites/page_site.html', {'site': site, 'error': req.GET.get('error')})

@login_required
def edit_site(req, site_slug):
    site = get_site(req, site_slug)

    data = {
        'site': site,
        'themes': Site.SITE_THEMES,
    }

    if not req.POST:
        return _pmrender(req, 'dashboard/sites/page_edit.html', data)

    try:
        site.slug = req.POST.get('slug')
        site.theme = req.POST.get('theme')
        site.cover_image_url = signer.unsign(req.POST.get('cover-url')) if req.POST.get('cover-url') else None
        site.logo_url = signer.unsign(req.POST.get('logo-url')) if req.POST.get('logo-url') else None
        site.analytics_id = req.POST.get('analytics_id')
        site.save()
    except Exception as e:
        print e
        data.update(error=True, default=req.POST)
        return _pmrender(req, 'dashboard/sites/page_edit.html', data)
    else:
        return redirect('site_options', site_slug=site.slug)

@login_required
def delete_site(req, site_slug):
    site = get_site(req, site_slug)

    data = {'site': site}

    if not req.POST:
        return _pmrender(req, 'dashboard/sites/page_delete.html', data)

    podcast_slug = site.podcast.slug
    site.delete()
    return redirect('podcast_dashboard', podcast_slug=podcast_slug, tab='tab-site')


@login_required
@require_POST
def add_link(req, site_slug):
    site = get_site(req, site_slug)

    try:
        link = SiteLink(
            site=site,
            title=req.POST.get('title'),
            url=req.POST.get('url')
        )
        link.save()
        return redirect('site_options', site_slug=site_slug)
    except Exception as e:
        print e
        return redirect(reverse('site_options', site_slug=site_slug) + '?error=link')

@login_required
@require_POST
def remove_link(req, site_slug):
    site = get_site(req, site_slug)
    try:
        link = SiteLink.objects.get(id=req.POST.get('id'))
        link.delete()
    except Exception:
        pass
    return redirect('site_options', site_slug=site_slug)

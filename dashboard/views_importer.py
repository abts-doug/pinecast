import datetime
import json
import time

import requests
from defusedxml.minidom import parseString as parseXMLString
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import importer as importer_lib
from . import importer_worker
from .models import AssetImportRequest
from .views import _pmrender, json_response
from podcasts.models import Podcast, PodcastEpisode


@login_required
def importer(req):
    if not req.POST:
        return _pmrender(req, 'dashboard/importer.html')
    return _pmrender(req, 'dashboard/importer.html')

@login_required
@json_response
@importer_lib.handle_format_exceptions
def importer_lookup(req):
    url = req.GET.get('url')
    if not url:
        return {'error': 'no url'}

    if url.startswith('feed://'):
        url = 'http://' + url[7:]
    if not url.startswith('http://') and not url.startswith('https://'):
        return {'error': 'protocol'}

    try:
        data = requests.get(url, timeout=5)
    except Exception as e:
        print e
        return {'error': 'connection'}
    
    try:
        encoded = data.text.encode(data.encoding or 'utf-8')
    except Exception as e:
        print e
        return {'error': 'invalid encoding'}
    
    try:
        parsed = parseXMLString(encoded)
    except Exception as e:
        print e
        return {'error': 'invalid xml'}

    return importer_lib.get_details(req, parsed)


@login_required
@json_response
def start_import(req):
    try:
        parsed_items = json.loads(req.POST.get('items'))
    except Exception:
        return {'error': 'Invalid JSON'}


    asset_requests = []

    show_image_url = req.POST.get('cover_image')
    try:
        p = Podcast(
            owner=req.user,
            slug=req.POST.get('slug'),
            name=req.POST.get('name'),
            homepage=req.POST.get('homepage'),
            # TODO: convert this to markdown?
            description=req.POST.get('description'),
            language=req.POST.get('language'),
            copyright=req.POST.get('copyright'),
            subtitle=req.POST.get('subtitle'),
            author_name=req.POST.get('author_name'),
            is_explicit=req.POST.get('is_explicit', 'false') == 'true',

            # This is just temporary for the feed, just so it's usable in the interim
            cover_image=show_image_url,
        )
        p.save()
        p.set_category_list(req.POST.get('categories'))

        imp_req = AssetImportRequest.create(
            podcast=p,
            expiration=datetime.datetime.now() + datetime.timedelta(hours=1),
            image_source_url=p.cover_image)
        asset_requests.append(imp_req)
    except Exception as e:
        if p:
            try:
                p.delete()
            except Exception:
                pass
        return {'error': 'There was a problem saving the podcast: %s' % str(e)}

    created_items = []
    try:
        for item in parsed_items:
            i = PodcastEpisode(
                podcast=p,
                title=item['title'],
                subtitle=item['subtitle'],
                publish=datetime.datetime.fromtimestamp(time.mktime(item['publish'])),
                description=item['description'],  # TODO: convert to markdown?
                duration=int(item['duration']),
                audio_url=item['audio_url'],
                audio_size=int(item['audio_size']),
                audio_type=item['audio_type'],
                image_url=item['image_url'] or show_image_url,
                copyright=item['copyright'],
                license=item['license'],
                awaiting_import=True)
            i.save()
            created_items.append(i)

            # Audio import request
            imp_req = AssetImportRequest.create(
                episode=i,
                expiration=datetime.datetime.now() + datetime.timedelta(hours=3),
                audio_source_url=i.audio_url)
            asset_requests.append(imp_req)


            if i.image_url == p.cover_image: continue

            # Image import request
            imp_req = AssetImportRequest.create(
                episode=i,
                expiration=datetime.datetime.now() + datetime.timedelta(hours=3),
                image_source_url=i.image_url)
            asset_requests.append(imp_req)

    except Exception as e:
        p.delete()
        for i in created_items:
            try:
                i.delete()
            except Exception:
                pass
        return {'error': 'There was a problem saving the podcast items: %s' % str(e)}

    for ir in asset_requests:
        ir.save()

    payloads = (x.get_payload() for x in asset_requests)
    payloads = importer_worker.prep_payloads(payloads)
    importer_worker.push_batch(settings.SNS_IMPORT_BUS, payloads)

    return {'error': False, 'ids': [x.id for x in asset_requests]}


@login_required
@json_response
def import_progress(req, podcast_slug):
    p = get_object_or_404(Podcast, slug=podcast_slug, owner=req.user)
    ids = req.GET.get('ids')
    reqs = AssetImportRequest.objects.filter(id__in=ids.split(','))
    total = reqs.count()
    return {'status': sum(1.0 for r in reqs if r.resolved) / total * 100.0}


@csrf_exempt
@require_POST
@json_response
def import_result(req):
    p = get_object_or_404(AssetImportRequest,
                          access_token=req.POST.get('token'),
                          id=req.POST.get('id'))

    if req.POST.get('failed'):
        p.failure_message = req.POST.get('error')
        p.save()
        return {'success': True}

    try:
        p.resolve(req.POST.get('url'))
    except Exception as e:
        return HttpResponseBadRequest(str(e))

    return {'success': True}

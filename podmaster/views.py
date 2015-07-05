import json

import requests
from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import analytics.analyze as analyze
import analytics.log as analytics_log
from podcasts.models import Podcast, PodcastEpisode


@csrf_exempt
@require_POST
def deploy_complete(req):

    commit = '<https://github.com/AlmostBetterNetwork/podmaster-host/commit/%s|%s>' % (
        req.POST.get('head'), req.POST.get('head'))

    payload = {
        'text': '''
            Hey guys! I'm PodMaster Host version %s. I was just born! :hatching_chick:
You have %s to thank for pushing %s to production.
To learn about what's new, check out #podmaster-hosting :two_hearts:
        '''.strip() % (req.POST.get('release'), req.POST.get('user'), commit),
        'username': 'newborn-podmaster-host',
        'icon_emoji': ':cat2:',
    }

    print requests.post(
        settings.DEPLOY_SLACKBOT_URL,
        data={'payload': json.dumps(payload)})

    return HttpResponse(status=204)


class FakeReq(object):
    def __init__(self, blob):
        self.META = {'HTTP_USER_AGENT': blob['userAgent'],
                     'REMOTE_ADDR': blob['ip']}


@csrf_exempt
def log(req):
    if req.GET.get('access') != settings.LAMBDA_ACCESS_SECRET:
        return HttpResponse(status=400)

    try:
        parsed = json.loads(req.POST.get('payload'))
    except Exception:
        return HttpResponse(status=400)

    for blob in parsed: # TODO: this can throw an exception
        fr = FakeReq(blob)
        if analyze.is_bot(fr):
            continue

        try:
            ep = PodcastEpisode.objects.get(id=blob['episode'])
        except PodcastEpisode.DoesNotExist:
            continue

        browser, device, os = analyze.get_device_type(fr)
        print 'Logged record of listen for %s' % unicode(ep.id)
        analytics_log.write('listen', {
            'podcast': unicode(ep.podcast.id),
            'episode': unicode(ep.id),
            'source': blob.get('source'),
            'profile': {
                'ip': blob.get('ip'),
                'ua': blob.get('userAgent'),
                'browser': browser,
                'device': device,
                'os': os,
            },
        })

    return HttpResponse(status=204)

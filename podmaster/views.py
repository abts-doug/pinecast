import json

import requests
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


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

    return HttpResponse('Thanks! <3')

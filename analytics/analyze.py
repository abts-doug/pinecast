import base64
import datetime

from user_agents import parse


def get_device_type(req):
    parsed = _parse_req(req)
    return parsed.browser.family, parsed.device.family, parsed.os.family


def is_bot(req):
    return _parse_req(req).is_bot


def _parse_req(req):
    if not hasattr(req, '__parsed_ua'):
        setattr(req, '__parsed_ua', parse(req.META['HTTP_USER_AGENT']))
    return getattr(req, '__parsed_ua')


def get_request_ip(req):
    x_forwarded_for = req.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    
    return req.META.get('REMOTE_ADDR')


def get_request_hash(req):
    ua = req.META.get('HTTP_USER_AGENT')
    ip = get_request_ip(req)
    today = datetime.date.today().isoformat()
    return base64.b64encode('%s:%s:%s' % (today, ip, ua))

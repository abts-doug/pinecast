from user_agents import parse


def get_device_type(req):
    parsed = _parse_req(req)
    return parsed.browser.family, parsed.device.family, parsed.os.family


def is_bot(req):
    return _parse_req(req.META['HTTP_USER_AGENT']).is_bot


def _parse_req(req):
    if not req.__parsed_ua:
        req.__parsed_ua = parse(req.META['HTTP_USER_AGENT'])
    return req.__parsed_ua

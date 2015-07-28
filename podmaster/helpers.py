from functools import wraps

import django.core.urlresolvers
from django.core.urlresolvers import reverse as reverse_django


def json_response(*args, **jr_kwargs):
    def wrapper(view):
        @wraps(view)
        def func(*args, **kwargs):
            resp = view(*args, **kwargs)
            if not isinstance(resp, dict):
                # Handle HttpResponse/HttpResponseBadRequest/etc
                return resp
            return JsonResponse(resp, safe=jr_kwargs.get('safe', True))
        return func
    return wrapper if jr_kwargs else wrapper(*args)


@wraps(reverse_django)
def reverse(viewname, kwargs=None, **kw):
    if kwargs is None:
        kwargs = {}
    kwargs.update(kw)
    return reverse_django(viewname, kwargs=kwargs)

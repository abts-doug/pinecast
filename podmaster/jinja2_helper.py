from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.urlresolvers import reverse
from jinja2 import Environment


def environment(**options):
    options['autoescape'] = True
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'str': str,
        'url': reverse,
    })
    return env

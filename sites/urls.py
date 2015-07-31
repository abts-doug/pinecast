from django.conf.urls import include, url

import urls_internal
from . import views


urlpatterns = [
    url(r'^(?P<site_slug>[\w-]+)/', include(urls_internal)),
]

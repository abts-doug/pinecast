from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import redirect

import analytics.urls
import dashboard.urls
from podcasts.urls import urlpatterns as podcast_urlpatterns


logout_view = lambda r: logout(r) or redirect('home')


urlpatterns = podcast_urlpatterns + [
    url(r'^logout$', logout_view, name='logout'),
    url(r'^analytics/', include(analytics.urls)),
    url(r'^dashboard/', include(dashboard.urls)),
    url(r'^admin/', include(admin.site.urls)),
]

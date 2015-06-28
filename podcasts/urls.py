from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^feed/(?P<podcast_slug>[\w-]+)$', views.feed),
]

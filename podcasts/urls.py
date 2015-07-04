from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^listen/(?P<episode_id>[\w-]+)$', views.listen, name='listen'),
    url(r'^feed/(?P<podcast_slug>[\w-]+)$', views.feed, name='feed'),
]

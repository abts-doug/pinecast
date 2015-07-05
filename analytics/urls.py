from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^podcast-subscriber-history$', views.podcast_subscriber_history),
    url(r'^podcast-listen-history$', views.podcast_listen_history),
    url(r'^episode-listen-history$', views.episode_listen_history),
    url(r'^podcast-listen-breakdown$', views.podcast_listen_breakdown),
    url(r'^episode-listen-breakdown$', views.episode_listen_breakdown),
]

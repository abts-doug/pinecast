from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.site_home, name='site_home'),
    url(r'^episode/(?P<episode_id>[\w-]+)$', views.site_episode, name='site_episode'),
    url(r'^blog/(?P<post_slug>[\w-]+)$', views.site_post, name='site_post'),
]

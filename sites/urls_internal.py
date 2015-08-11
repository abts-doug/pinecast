from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.site_home, name='site_home'),
    url(r'^blog$', views.site_blog, name='site_blog'),
    url(r'^blog/(?P<post_slug>[\w-]+)$', views.site_post, name='site_post'),
]

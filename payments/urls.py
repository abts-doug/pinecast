from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^upgrade$', views.upgrade, name='upgrade'),
]

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^upgrade$', views.upgrade, name='upgrade'),
    url(r'^services/set_payment_method$', views.set_payment_method, name='set_payment_method'),
]

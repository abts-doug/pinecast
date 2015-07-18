from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^login$', views.login_page, name='login'),
    url(r'^beta_signup$', views.private_beta_signup, name='beta_signup'),
]

from django.conf.urls import url

from . import views, views_importer


urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^new_podcast$', views.new_podcast, name='new_podcast'),
    url(r'^podcast/(?P<podcast_slug>[\w-]+)$', views.podcast_dashboard, name='podcast_dashboard'),
    url(r'^podcast/(?P<podcast_slug>[\w-]+)/delete$', views.delete_podcast, name='delete_podcast'),
    url(r'^podcast/(?P<podcast_slug>[\w-]+)/edit$', views.edit_podcast, name='edit_podcast'),
    url(r'^podcast/(?P<podcast_slug>[\w-]+)/geo$', views.podcast_new_ep, name='new_episode'),
    url(r'^podcast/(?P<podcast_slug>[\w-]+)/new_episode$', views.podcast_geochart, name='podcast_geo'),
    url(r'^podcast/(?P<podcast_slug>[\w-]+)/top$', views.podcast_top_episodes, name='top_episodes'),
    url(r'^podcast/(?P<podcast_slug>[\w-]+)/episode/(?P<episode_id>[\w-]+)$', views.podcast_episode, name='podcast_episode'),
    url(r'^podcast/(?P<podcast_slug>[\w-]+)/episode/(?P<episode_id>[\w-]+)/delete$', views.delete_podcast_episode, name='delete_podcast_episode'),
    url(r'^podcast/(?P<podcast_slug>[\w-]+)/episode/(?P<episode_id>[\w-]+)/edit$', views.edit_podcast_episode, name='edit_podcast_episode'),

    url(r'^import$', views_importer.importer, name='importer'),
    url(r'^import/feed$', views_importer.importer_lookup),

    url(r'^services/slug_available$', views.slug_available, name='slug_available'),
    url(r'^services/getUploadURL/(?P<podcast_slug>([\w-]+|\$none))/(?P<type>[\w]+)$', views.get_upload_url, name='get_upload_url'),

    url(r'^services/start_import$', views_importer.start_import),
    url(r'^services/import_progress/(?P<podcast_slug>[\w-]+)$', views_importer.import_progress),
    url(r'^services/import_result$', views_importer.import_result),
    url(r'^services/get_request_token$', views_importer.get_request_token),
    url(r'^services/check_request_token$', views_importer.check_request_token),
]

import datetime
import uuid

from django.conf import settings
from django.db import models

import importer_worker
from podcasts.models import Podcast, PodcastEpisode


class AssetImportRequest(models.Model):
    created = models.DateTimeField(auto_now=True)

    podcast = models.ForeignKey(Podcast, null=True)
    episode = models.ForeignKey(PodcastEpisode, null=True)

    expiration = models.DateTimeField()
    audio_source_url = models.URLField(blank=True)
    image_source_url = models.URLField(blank=True)
    access_token = models.CharField(max_length=128)

    resolved = models.BooleanField(default=False)

    failed = models.BooleanField(default=False)
    failure_message = models.TextField(null=True)

    @classmethod
    def create(cls, *args, **kwargs):
        if 'access_token' not in kwargs:
            kwargs['access_token'] = AssetImportRequest.get_token()
        return cls(*args, **kwargs)

    @classmethod
    def get_token(cls):
        return unicode(uuid.uuid4())

    def resolve(self, new_url):
        if self.resolved:
            raise Exception('Attempting to double-resolve import request')

        if self.expired < datetime.datetime.now():
            raise Exception('Attempting to resolve expired import request')

        if self.podcast:
            if self.audio_source_url:
                raise Exception('Invalid import request')

            orig_url = self.podcast.cover_image
            self.podcast.cover_image = new_url
            self.podcast.save()

            eps = self.podcast.podcastepisode_set.filter(image_url=orig_url)
            for ep in eps:
                ep.image_url = new_url
                ep.save()

        elif self.episode:
            if self.audio_source_url:
                self.episode.audio_url = new_url
            else:
                self.episode.image_url = new_url

            if (settings.S3_BUCKET in self.episode.audio_url and
                settings.S3_BUCKET in self.episode.image_url):
                self.episode.awaiting_import = False
            self.episode.save()

        else:
            raise Exception('Invalid import request for neither podcast nor ep')

        self.resolved = True
        self.save()

    def get_payload(self):
        source = self.audio_source_url or self.image_source_url
        if self.podcast:
            key = 'podcasts/covers/'
        else:
            key = 'podcasts/%s/%s/' % (
                str(self.episode.podcast.id),
                'image' if self.image_source_url else 'audio')
        key = '%s%s/%s' % (key, str(uuid.uuid4()), source[source.rindex('/') + 1:])
        return {
            'type': 'import_asset',
            'token': self.access_token,
            'id': self.id,
            'url': source,
            'bucket': settings.S3_BUCKET,
            'key': key,
        }

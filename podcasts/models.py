import datetime
import uuid

from django.contrib.auth.models import User
from django.db import models


class Podcast(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)

    name = models.CharField(max_length=256)
    subtitle = models.CharField(max_length=512, default='')

    created = models.DateTimeField(auto_now=True)
    cover_image = models.URLField()
    description = models.TextField()
    is_explicit = models.BooleanField()
    homepage = models.URLField()

    language = models.CharField(max_length=16)
    copyright = models.CharField(max_length=1024)
    author_name = models.CharField(max_length=1024)

    owner = models.ForeignKey(User)

    def __unicode__(self):
        return self.name


class PodcastEpisode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    podcast = models.ForeignKey(Podcast)
    title = models.CharField(max_length=1024)
    subtitle = models.CharField(max_length=1024, default='')
    created = models.DateTimeField(auto_now=True)
    publish = models.DateTimeField()
    description = models.TextField(default='')
    duration = models.PositiveIntegerField(help_text='Audio duration in seconds')

    audio_url = models.URLField()
    audio_size = models.PositiveIntegerField(default=0)
    audio_type = models.CharField(max_length=64)

    image_url = models.URLField()

    copyright = models.CharField(max_length=1024)
    license = models.CharField(max_length=1024)

    def is_published(self):
        return self.publish <= datetime.now()

    def __unicode__(self):
        return '%s - %s' % (self.title, self.subtitle)

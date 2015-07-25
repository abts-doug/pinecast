from boto.s3.connection import S3Connection
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from podcasts.models import Podcast, PodcastEpisode


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('--run',
            action='store_true',
            dest='run',
            default=False,
            help='Actually runs the command instead of doing a dry run')

    def handle(self, *args, **options):
        self.stdout.write('Downloading S3 manifest...')
        conn = S3Connection(settings.S3_ACCESS_ID, settings.S3_SECRET_KEY)
        bucket = conn.get_bucket(settings.S3_BUCKET)
        files = bucket.list()

        for f in files:
            canon_url = 'http://%s.s3.amazonaws.com/%s' % (settings.S3_BUCKET, f.key)
            self.stdout.write(' - %s' % canon_url)
            if (f.key.startswith('podcasts/covers/') and
                Podcast.objects.filter(cover_image=canon_url).count()):
                self.stdout.write('     Still in use by Podcast')
                continue

            if PodcastEpisode.objects.filter(
                Q(audio_url=canon_url) | Q(image_url=canon_url)).count():
                self.stdout.write('     Still in use by PodcastEpisode')

            self.stdout.write('     No longer in use!')

            if options['run']:
                f.delete()

        self.stdout.write('Completed')

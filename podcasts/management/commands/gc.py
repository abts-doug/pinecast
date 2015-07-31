from boto.s3.connection import S3Connection
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from accounts.models import Network
from podcasts.models import Podcast, PodcastEpisode


class Command(BaseCommand):
    help = 'Removes unreferenced files from the S3 bucket'

    def add_arguments(self, parser):
        parser.add_argument('--run',
            action='store_true',
            dest='run',
            default=False,
            help='Actually runs the command instead of doing a dry run')

    def handle(self, *args, **options):
        conn = S3Connection(settings.S3_ACCESS_ID, settings.S3_SECRET_KEY)

        self.clean_bucket(conn, settings.S3_BUCKET, options)
        self.clean_bucket(conn, settings.S3_PREMIUM_BUCKET, options)

    def clean_bucket(conn, bucket_name, options):
        self.stdout.write('Processing bucket: %s' % bucket_name)
        self.stdout.write('Downloading S3 manifest...')
        bucket = conn.get_bucket(bucket_name)
        files = bucket.list()

        to_delete = []

        self.stdout.write('Analyzing bucket contents...')
        for f in files:
            canon_url = 'http://%s.s3.amazonaws.com/%s' % (settings.S3_BUCKET, f.key)
            self.stdout.write(' - %s' % canon_url)

            if (f.key.startswith('networks/covers/') and
                Network.objects.filter(image_url=canon_url).count()):
                self.stdout.write('     Still in use by Network')
                continue

            if (f.key.startswith('podcasts/covers/') and
                Podcast.objects.filter(cover_image=canon_url).count()):
                self.stdout.write('     Still in use by Podcast')
                continue

            if PodcastEpisode.objects.filter(
                Q(audio_url=canon_url) | Q(image_url=canon_url)).count():
                self.stdout.write('     Still in use by PodcastEpisode')
                continue

            to_delete.append(f)

        self.stdout.write('Completed analysis')
        self.stdout.write('%d files to remove' % len(to_delete))
        if options['run']:
            for f in to_delete:
                f.delete()
            self.stdout.write('Completed removal')
        else:
            self.stdout.write('No files were removed. Use --run to actually GC')

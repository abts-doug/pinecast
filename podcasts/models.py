import datetime
import uuid

from django.contrib.auth.models import User
from django.db import models

from accounts.models import Network


class Podcast(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)

    name = models.CharField(max_length=256)
    subtitle = models.CharField(max_length=512, default='', blank=True)

    created = models.DateTimeField(auto_now=True)
    cover_image = models.URLField()
    description = models.TextField()
    is_explicit = models.BooleanField()
    homepage = models.URLField()

    language = models.CharField(max_length=16)
    copyright = models.CharField(max_length=1024)
    author_name = models.CharField(max_length=1024)

    owner = models.ForeignKey(User)

    rss_redirect = models.URLField(null=True)
    stats_base_listens = models.PositiveIntegerField(default=0)

    networks = models.ManyToManyField(Network)


    def get_category_list(self):
        return ','.join(x.category for x in self.podcastcategory_set.all())

    def set_category_list(self, cat_str):
        existing = set(x.category for x in self.podcastcategory_set.all())
        new = set(cat_str.split(','))

        added = new - existing
        removed = existing - new

        for a in added:
            n = PodcastCategory(podcast=self, category=a)
            n.save()

        for r in removed:
            o = PodcastCategory.objects.get(podcast=self, category=r)
            o.delete()

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
    license = models.CharField(max_length=1024, blank=True)

    awaiting_import = models.BooleanField(default=False)


    def is_published(self):
        return not self.awaiting_import and self.publish <= datetime.datetime.now()

    def __unicode__(self):
        return '%s - %s' % (self.title, self.subtitle)


class EpisodeImportRequest(models.Model):
    episode = models.ForeignKey(PodcastEpisode)
    expiration = models.DateTimeField()
    audio_source_url = models.URLField()
    image_source_url = models.URLField(blank=True)
    access_token = models.CharField(max_length=128)


CATEGORIES = set([
    'Arts',
    'Arts/Design',
    'Arts/Fashion & Beauty',
    'Arts/Food',
    'Arts/Literature',
    'Arts/Performing Arts',
    'Arts/Spoken Word',
    'Arts/Visual Arts',
    'Business',
    'Business/Business News',
    'Business/Careers',
    'Business/Investing',
    'Business/Management & Marketing',
    'Business/Shopping',
    'Comedy',
    'Education',
    'Education/Educational Technology',
    'Education/Higher Education',
    'Education/K-12',
    'Education/Language Courses',
    'Education/Training',
    'Games & Hobbies',
    'Games & Hobbies/Automotive',
    'Games & Hobbies/Aviation',
    'Games & Hobbies/Hobbies',
    'Games & Hobbies/Other Games',
    'Games & Hobbies/Video Games',
    'Government & Organizations',
    'Government & Organizations/Local',
    'Government & Organizations/National',
    'Government & Organizations/Non-Profit',
    'Government & Organizations/Regional',
    'Health',
    'Health/Alternative Health',
    'Health/Fitness & Nutrition',
    'Health/Self-Help',
    'Health/Sexuality',
    'Health/Kids & Family',
    'Music',
    'Music/Alternative',
    'Music/Blues',
    'Music/Country',
    'Music/Easy Listening',
    'Music/Electronic',
    'Music/Electronic/Acid House',
    'Music/Electronic/Ambient',
    'Music/Electronic/Big Beat',
    'Music/Electronic/Breakbeat',
    'Music/Electronic/Disco',
    'Music/Electronic/Downtempo',
    'Music/Electronic/Drum \'n\' Bass',
    'Music/Electronic/Garage',
    'Music/Electronic/Hard House',
    'Music/Electronic/House',
    'Music/Electronic/IDM',
    'Music/Electronic/Jungle',
    'Music/Electronic/Progressive',
    'Music/Electronic/Techno',
    'Music/Electronic/Trance',
    'Music/Electronic/Tribal',
    'Music/Electronic/Trip Hop',
    'Music/Folk',
    'Music/Freeform',
    'Music/Hip-Hop & Rap',
    'Music/Inspirational',
    'Music/Jazz',
    'Music/Latin',
    'Music/Metal',
    'Music/New Age',
    'Music/Oldies',
    'Music/Pop',
    'Music/R&B & Urban',
    'Music/Reggae',
    'Music/Rock',
    'Music/Seasonal & Holiday',
    'Music/Soundtracks',
    'Music/World',
    'News & Politics',
    'News & Politics/Conservative (Right)',
    'News & Politics/Liberal (Left)',
    'Religion & Spirituality',
    'Religion & Spirituality/Buddhism',
    'Religion & Spirituality/Christianity',
    'Religion & Spirituality/Hinduism',
    'Religion & Spirituality/Islam',
    'Religion & Spirituality/Judaism',
    'Religion & Spirituality/Other',
    'Religion & Spirituality/Spirituality',
    'Science & Medicine',
    'Science & Medicine/Medicine',
    'Science & Medicine/Natural Sciences',
    'Science & Medicine/Social Sciences',
    'Society & Culture',
    'Society & Culture/Gay & Lesbian',
    'Society & Culture/History',
    'Society & Culture/Personal Journals',
    'Society & Culture/Philosophy',
    'Society & Culture/Places & Travel',
    'Sports & Recreation',
    'Sports & Recreation/Amateur',
    'Sports & Recreation/College & High School',
    'Sports & Recreation/Outdoor',
    'Sports & Recreation/Professional',
    'TV & Film',
    'Technology',
    'Technology/Gadgets',
    'Technology/IT News',
    'Technology/Podcasting',
    'Technology/Software How-To',
])

class PodcastCategory(models.Model):
    category = models.CharField(max_length=128,
                                choices=[(x, x) for x in CATEGORIES])
    podcast = models.ForeignKey(Podcast)


    def __unicode__(self):
        return '%s: %s' % (self.podcast.name, self.category)

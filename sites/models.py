from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy

from podcasts.models import Podcast


BANNED_SLUGS = set([
    'about',
    'admin',
    'api',
    'apps',
    'asset-cdn',
    'asset-cdn-cf',
    'beta',
    'blog',
    'careers',
    'cdn',
    'chat',
    'community',
    'dmca',
    'download',
    'feed',
    'feedback',
    'feeds',
    'forum',
    'forums',
    'ftp',
    'help',
    'host',
    'jobs',
    'kb',
    'kits',
    'knowledgebase',
    'live',
    'm',
    'mail',
    'media',
    'mobile',
    'next',
    'pop',
    'search',
    'smtp',
    'status',
    'store',
    'support',
    'vpn',
    'webmail',
    'wiki',
    'www',
])

THEME_ABN = 'abn'
SECRET_THEMES = set([THEME_ABN])

class Site(models.Model):
    SITE_THEMES = (
        ('panther', ugettext_lazy('Panther')),
        ('podcasty', ugettext_lazy('Podcasty')),
        ('zen', ugettext_lazy('Zen')),
        ('wharf', ugettext_lazy('Wharf')),
        (THEME_ABN, ugettext_lazy('ABN')),
    )
    SITE_THEMES_MAP = {k: v for k, v in SITE_THEMES}
    SITE_THEMES_MAP_PUBLIC = {k: v for k, v in SITE_THEMES if k not in SECRET_THEMES}

    podcast = models.OneToOneField(Podcast)
    slug = models.SlugField(unique=True)
    theme = models.CharField(choices=SITE_THEMES, max_length=16)
    custom_cname = models.CharField(blank=True, null=True, max_length=64)
    cover_image_url = models.URLField(blank=True)
    logo_url = models.URLField(blank=True)
    itunes_url = models.URLField(blank=True)
    stitcher_url = models.URLField(blank=True)

    def clean(self):
        if self.slug in BANNED_SLUGS:
            raise ValidationError('Cannot choose that slug')

    def get_cover_style(self, bgcolor=None):
        if self.cover_image_url:
            return 'background-image: url(%s)' % self.cover_image_url
        elif bgcolor:
            return 'background-color: %s' % bgcolor
        else:
            return 'background-color: #666'

    def __unicode__(self):
        return '%s: %s' % (self.slug, self.podcast.name)


class SiteLink(models.Model):
    site = models.ForeignKey(Site)
    title = models.CharField(max_length=256)
    url = models.URLField(blank=True)
    class_name = models.CharField(max_length=256, blank=True, null=True)

class SiteBlogPost(models.Model):
    site = models.ForeignKey(Site)
    title = models.CharField(max_length=512)
    slug = models.SlugField()
    created = models.DateTimeField(auto_now=True)
    publish = models.DateTimeField()
    body = models.TextField()

    def __unicode__(self):
        return '%s on %s' % (self.slug, self.site.slug)

    class Meta:
        unique_together = (('site', 'slug'), )

import datetime
import time
from email.Utils import formatdate
from xml.sax.saxutils import escape, quoteattr

from django.http import Http404, HttpResponse

from .models import Podcast, PodcastEpisode


def feed(req, podcast_slug):
    try:
        pod = Podcast.objects.get(slug=podcast_slug)
    except Podcast.DoesNotExist:
        raise Http404('Podcast does not exist')

    items = []
    for ep in pod.podcastepisode_set.all():
        duration = datetime.timedelta(seconds=ep.duration)
        items.append('\n'.join([
            '<item>',
                '<title>%s</title>' % escape(ep.title),
                '<description><![CDATA[%s]]></description>' % ep.description,
                '<link>%s</link>' % escape(ep.audio_url),
                '<guid isPermaLink="false">http://almostbetter.net/guid/%s</guid>' % escape(str(ep.id)),
                '<pubDate>%s</pubDate>' % formatdate(time.mktime(ep.publish.timetuple())),
                '<itunes:author>%s</itunes:author>' % escape(pod.author_name),
                '<itunes:subtitle>%s</itunes:subtitle>' % escape(ep.subtitle),
                '<itunes:summary><![CDATA[%s]]></itunes:summary>' % ep.description,
                '<itunes:image href="%s" />' % quoteattr(ep.image_url),
                '<itunes:duration>%s</itunes:duration>' % escape(str(duration)),
                '<enclosure url="%s" length="%s" type="%s" />' % (
                    quoteattr(ep.audio_url), quoteattr(ep.audio_size), quoteattr(ep.audio_type)),
            '</item>',
        ]))

    content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">',
        '<channel>',
            '<title>%s</title>' % escape(pod.name),
            '<link>%s</link>' % escape(pod.homepage),
            '<language>%s</language>' % escape(pod.language),
            '<copyright>%s</copyright>' % escape(pod.copyright),
            '<itunes:subtitle>%s</itunes:subtitle>' % escape(pod.subtitle),
            '<itunes:author>%s</itunes:author>' % escape(pod.author_name),
            '<itunes:summary><![CDATA[%s]]></itunes:summary>' % pod.description,
            '<description><![CDATA[%s]]></description>' % pod.description,
            '<itunes:owner>',
                '<itunes:name>%s</itunes:name>' % escape(pod.author_name),
                '<itunes:email>%s</itunes:email>' % escape(pod.owner.email),
            '</itunes:owner>',
            '<itunes:explicit>%s</itunes:explicit>' % ('yes' if pod.is_explicit else 'no'),
            '<itunes:image href="%s" />' % quoteattr(pod.cover_image),
            '\n'.join(items),
        '</channel>',
        '</rss>',
    ]
    return HttpResponse('\n'.join(content), content_type='application/rss+xml')

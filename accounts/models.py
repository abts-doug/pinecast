import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy

import payment_plans
from pinecast.helpers import cached_method


class BetaRequest(models.Model):
    PODCASTER_TYPE = (
        ('HOBBYIST', ugettext_lazy('Hobbyist')),
        ('AUTHOR', ugettext_lazy('Author or Writer')),
        ('MUSICIAN', ugettext_lazy('Musician')),
        ('RADIO', ugettext_lazy('Radio Personality')),
        ('COMEDY', ugettext_lazy('Comedian')),
        ('POLITIC', ugettext_lazy('Politician')),
    )
    created = models.DateTimeField(auto_now=True)
    email = models.EmailField()
    podcaster_type = models.CharField(choices=PODCASTER_TYPE,
                                      max_length=max(len(x) for x, y in PODCASTER_TYPE))


class UserSettings(models.Model):
    user = models.OneToOneField(User)
    plan = models.PositiveIntegerField(default=0, choices=payment_plans.PLANS)
    tz_offset = models.SmallIntegerField(default=0)  # Default to UTC

    # CDN controls
    force_disable_cdn = models.BooleanField(default=False)
    force_enable_cdn = models.BooleanField(default=False)

    plan_podcast_limit_override = models.PositiveIntegerField(default=0)  # Podcast limit = max(pplo, plan.max)

    def clean(self):
        if self.tz_offset < -12 or self.tz_offset > 14:
            raise ValidationError('Timezone offset must be between -12 and 14, inclusive')

        if self.force_enable_cdn and self.force_disable_cdn:
            raise ValidationError('CDN cannot be both force disabled and enabled')

    @classmethod
    def get_from_user(cls, user):
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            us = UserSettings(user=user)
            us.save()
            return us

    @classmethod
    def user_meets_plan(cls, user, min_plan):
        uset = cls.get_from_user(user)
        return payment_plans.minimum(uset.plan, min_plan)

    @cached_method
    def use_cdn(self):
        if self.force_disable_cdn:
            return False
        elif self.force_enable_cdn:
            return True
        return payment_plans.minimum(self.plan, payment_plans.FEATURE_MIN_CDN)

    @cached_method
    def get_tz_delta(self):
        return datetime.timedelta(hours=self.tz_offset)


class Network(models.Model):
    owner = models.ForeignKey(User, related_name='network_ownership')
    name = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now=True)

    image_url = models.URLField(blank=True, null=True)
    deactivated = models.BooleanField(default=False)

    members = models.ManyToManyField(User)

    def __unicode__(self):
        return self.name

    @cached_method
    def get_member_count(self):
        return self.members.count()

    @cached_method
    def get_podcast_count(self):
        return self.podcast_set.count()

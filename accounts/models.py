import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy

import payment_plans
from pinecast.helpers import cached_method
from payments.stripe_lib import stripe


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

    plan_podcast_limit_override = models.PositiveIntegerField(default=0)  # Podcast limit = max(pplo, plan.max)

    ############################
    # Payments-related fields
    ############################

    stripe_customer_id = models.CharField(max_length=128, blank=True, null=True)
    stripe_payout_recipient = models.CharField(max_length=128, blank=True, null=True)


    def clean(self):
        if self.tz_offset < -12 or self.tz_offset > 14:
            raise ValidationError('Timezone offset must be between -12 and 14, inclusive')

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
    def get_tz_delta(self):
        return datetime.timedelta(hours=self.tz_offset)


    def get_stripe_customer(self):
        if self.stripe_customer_id:
            return stripe.Customer.retrieve(self.stripe_customer_id)

        return None

    def create_stripe_customer(self, token):
        if self.stripe_customer_id:
            self.get_stripe_customer().delete()

        customer = stripe.Customer.create(
            source=token,
            email=self.user.email,
            description=str(self.user.id))

        self.stripe_customer_id = customer.id
        self.save()


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

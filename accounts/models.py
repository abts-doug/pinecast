from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

import payment_plans


class BetaRequest(models.Model):
    PODCASTER_TYPE = (
        ('HOBBYIST', 'Hobbyist'),
        ('AUTHOR', 'Author or Writer'),
        ('MUSICIAN', 'Musician'),
        ('RADIO', 'Radio Personality'),
        ('COMEDY', 'Comedian'),
        ('POLITIC', 'Politician'),
    )
    created = models.DateTimeField(auto_now=True)
    email = models.EmailField()
    podcaster_type = models.CharField(choices=PODCASTER_TYPE,
                                      max_length=max(len(x) for x, y in PODCASTER_TYPE))


class UserSettings(models.Model):
    user = models.OneToOneField(User)
    plan = models.PositiveIntegerField(default=0, choices=payment_plans.PLANS)
    tz_offset = models.SmallIntegerField(default=0)  # Default to UTC

    def clean(self):
        if self.tz_offset < -12 or self.tz_offset > 14:
            raise ValidationError('Timezone offset must be between -12 and 14, inclusive')


class Network(models.Model):
    owner = models.ForeignKey(User, related_name='network_ownership')
    name = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now=True)

    image_url = models.URLField(blank=True)

    members = models.ManyToManyField(User)

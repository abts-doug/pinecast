# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20150901_1613'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='stripe_customer_id',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
    ]

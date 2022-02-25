# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mailer', '0003_auto_20151030_1418'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='reply_to',
            field=models.TextField(verbose_name='Reply to', blank=True, null=True),
        ),
    ]

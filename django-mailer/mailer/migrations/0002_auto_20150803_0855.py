# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('mailer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='message',
            name='object_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='tag',
            field=models.SlugField(blank=True, null=True),
        ),
    ]

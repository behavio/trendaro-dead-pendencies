# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('slug', models.SlugField(verbose_name='Slug', max_length=100, unique=True)),
                ('subject', models.CharField(verbose_name='Subject', max_length=100)),
                ('html_body', models.TextField(verbose_name='HTML body')),
            ],
            options={
                'verbose_name': 'E-mail',
                'verbose_name_plural': 'E-mails',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('message_data', models.TextField()),
                ('priority', models.PositiveSmallIntegerField(verbose_name='Priority', default=2, choices=[(1, 'High'), (2, 'Medium'), (3, 'Low')])),
                ('status', models.PositiveIntegerField(verbose_name='Status', default=0, choices=[(0, 'Pending'), (1, 'Sent'), (2, 'Deferred')])),
                ('created', models.DateTimeField(verbose_name='Created', default=django.utils.timezone.now)),
                ('updated', models.DateTimeField(verbose_name='Updated', auto_now=True)),
                ('recipients', models.TextField(verbose_name='Recipients', blank=True, null=True)),
                ('subject', models.TextField(verbose_name='Subject', blank=True, null=True)),
            ],
            options={
                'verbose_name': 'message',
                'verbose_name_plural': 'messages',
            },
        ),
    ]

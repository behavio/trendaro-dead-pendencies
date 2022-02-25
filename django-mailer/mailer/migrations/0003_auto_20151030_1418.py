# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mailer', '0002_auto_20150803_0855'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailtemplate',
            name='id',
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='slug',
            field=models.SlugField(primary_key=True, serialize=False, verbose_name='Slug', max_length=100),
        ),
    ]

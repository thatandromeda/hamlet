# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-29 13:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('citations', '0002_auto_20180319_2044'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='citation',
            options={'ordering': ['raw_ref']},
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-19 20:00
from __future__ import unicode_literals

from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('theses', '0007_remove_thesis__vector'),
    ]

    operations = [
        migrations.CreateModel(
            name='Citation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doi', models.CharField(max_length=66)),
                ('journal', models.TextField()),
                ('url', models.URLField()),
                ('author', models.TextField()),
                ('title', models.TextField()),
                ('isbn', models.CharField(max_length=20)),
                ('publisher', models.CharField(max_length=32)),
                ('year', models.CharField(max_length=4)),
                ('raw_ref', models.TextField()),
                ('thesis', models.ForeignKey(on_delete=models.CASCADE, to='theses.Thesis')),
            ],
        ),
    ]

# Generated by Django 3.1.1 on 2020-09-22 23:37

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Sobti', '0002_auto_20200922_1857'),
    ]

    operations = [
        migrations.AddField(
            model_name='glyph',
            name='shape',
            field=django.contrib.gis.db.models.fields.LineStringField(blank=True, null=True, srid=4326),
        ),
    ]
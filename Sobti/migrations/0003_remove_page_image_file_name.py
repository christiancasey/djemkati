# Generated by Django 3.0.5 on 2020-05-07 23:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Sobti', '0002_auto_20200507_1930'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='image_file_name',
        ),
    ]

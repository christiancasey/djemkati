# Generated by Django 3.0.5 on 2020-05-07 23:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Sobti', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='manuscript',
            name='image',
        ),
        migrations.RemoveField(
            model_name='manuscript',
            name='image_preview',
        ),
    ]

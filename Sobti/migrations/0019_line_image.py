# Generated by Django 3.0.5 on 2020-05-08 04:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Sobti', '0018_layer_page'),
    ]

    operations = [
        migrations.AddField(
            model_name='line',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]

# Generated by Django 3.0.5 on 2020-05-08 02:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Sobti', '0007_glyph_number_in_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='glyph',
            name='number_in_page',
            field=models.IntegerField(default=0, null=True, verbose_name='Sequence of glyph in page'),
        ),
    ]

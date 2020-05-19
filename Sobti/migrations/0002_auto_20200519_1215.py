# Generated by Django 3.0.5 on 2020-05-19 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Sobti', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manuscript',
            name='accession_number',
            field=models.CharField(blank=True, max_length=200, verbose_name='Accession number'),
        ),
        migrations.AlterField(
            model_name='text',
            name='title',
            field=models.CharField(max_length=200, verbose_name='Name of text'),
        ),
    ]
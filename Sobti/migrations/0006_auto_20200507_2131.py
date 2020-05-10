# Generated by Django 3.0.5 on 2020-05-08 01:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Sobti', '0005_auto_20200507_2121'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='glyph',
            name='image_file_name',
        ),
        migrations.AddField(
            model_name='glyph',
            name='image',
            field=models.ImageField(blank=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='line',
            name='image',
            field=models.ImageField(blank=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='glyph',
            name='mainz_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='Entry number in Mainz Palaeographie'),
        ),
        migrations.AlterField(
            model_name='glyph',
            name='manuel_de_codage',
            field=models.CharField(blank=True, max_length=100, verbose_name='Manuel de Codage hieroglyphs'),
        ),
        migrations.AlterField(
            model_name='glyph',
            name='moller_number',
            field=models.CharField(blank=True, max_length=50, verbose_name="Entry number in Möller's Palaeographie"),
        ),
        migrations.AlterField(
            model_name='glyph',
            name='polygon',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Sobti.Polygon'),
        ),
        migrations.AlterField(
            model_name='glyph',
            name='unicode_glyphs',
            field=models.CharField(blank=True, max_length=50, verbose_name='Unicode hieroglyphs'),
        ),
        migrations.AlterField(
            model_name='line',
            name='number_in_manuscript',
            field=models.IntegerField(null=True, verbose_name='Sequence of line in manuscript as a whole'),
        ),
    ]

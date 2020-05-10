# Generated by Django 3.0.5 on 2020-05-07 23:21

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, verbose_name='Museum or private collection')),
            ],
        ),
        migrations.CreateModel(
            name='Manuscript',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.FileField(blank=True, upload_to='upload/%Y-%m-%d')),
                ('image_preview', models.ImageField(blank=True, upload_to='')),
                ('accession_number', models.CharField(blank=True, max_length=200, verbose_name='Acquisition number in collection if available')),
                ('find_date', models.CharField(blank=True, max_length=300, verbose_name='Date found in modern era')),
                ('provenance', models.CharField(blank=True, max_length=200, verbose_name='Geographic location of origin')),
                ('date_added', models.DateTimeField(blank=True, default=django.utils.timezone.now, verbose_name='Date added to the database')),
                ('marked_for_deletion', models.BooleanField(default=False, verbose_name='Removing a text triggers more operations')),
                ('collection', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='Sobti.Collection')),
            ],
        ),
        migrations.CreateModel(
            name='Polygon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('polygon_type', models.CharField(blank=True, max_length=16, verbose_name='Type of polygon (line or glyph)')),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oclc', models.CharField(blank=True, max_length=500, verbose_name='OCLC of source.')),
            ],
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Name of composition')),
                ('era_composed', models.CharField(blank=True, max_length=200, verbose_name="Approximate date of the text's original composition")),
            ],
        ),
        migrations.CreateModel(
            name='PolygonPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('x_coordinate', models.IntegerField()),
                ('y_coordinate', models.IntegerField()),
                ('t_coordinate', models.IntegerField(verbose_name='Position in sequence of points')),
                ('polygon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sobti.Polygon')),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.FileField(blank=True, upload_to='upload/%Y-%m-%d')),
                ('image_preview', models.ImageField(blank=True, upload_to='')),
                ('image_thumbnail', models.ImageField(blank=True, upload_to='')),
                ('horizont', models.BooleanField(default=True, verbose_name='Text is horizontal (not vertical)')),
                ('number_in_manuscript', models.IntegerField(verbose_name='Sequence of page in manuscript')),
                ('image_file_name', models.CharField(default='dummy_text.png', max_length=300, verbose_name='Name of page image minus extension')),
                ('manuscript', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sobti.Manuscript')),
            ],
        ),
        migrations.AddField(
            model_name='manuscript',
            name='text',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sobti.Text'),
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number_in_page', models.IntegerField(verbose_name='Sequence of line in page')),
                ('number_in_manuscript', models.IntegerField(verbose_name='Sequence of line in manuscript as a whole')),
                ('image_file_name', models.CharField(blank=True, max_length=300, verbose_name='Name of line image minus extension')),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sobti.Page')),
                ('polygon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sobti.Polygon')),
            ],
        ),
        migrations.CreateModel(
            name='Glyph',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number_in_line', models.IntegerField(verbose_name='Sequence of glyph in line')),
                ('image_file_name', models.CharField(max_length=300, verbose_name='Name of glyph image minus extension')),
                ('unicode_glyphs', models.CharField(max_length=50, verbose_name='Unicode hieroglyphs')),
                ('manuel_de_codage', models.CharField(max_length=100, verbose_name='Manuel de Codage hieroglyphs')),
                ('moller_number', models.CharField(max_length=50, verbose_name="Entry number in Möller's Palaeographie")),
                ('mainz_number', models.CharField(max_length=100, verbose_name='Entry number in Mainz Palaeographie')),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sobti.Line')),
                ('polygon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sobti.Polygon')),
            ],
        ),
        migrations.CreateModel(
            name='BibEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sobti.Source')),
                ('text', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Sobti.Text')),
            ],
        ),
    ]

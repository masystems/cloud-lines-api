# Generated by Django 3.2.5 on 2021-09-15 20:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ExportQueue',
        ),
    ]
# Generated by Django 2.2.7 on 2020-04-09 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LiveStreamApp', '0011_auto_20200409_1053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='peer',
            name='login',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='peer',
            name='logout',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

# Generated by Django 4.1.4 on 2023-01-03 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="meeting",
            name="presentation_url",
            field=models.URLField(
                blank=True,
                help_text="The URL to the meeting's slideshow presentation if exists",
            ),
        ),
    ]
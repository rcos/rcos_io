# Generated by Django 4.1.4 on 2023-01-24 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0008_alter_user_options_alter_projecttag_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='projecttag',
            name='icon',
            field=models.CharField(default='devicon', max_length=100),
            preserve_default=False,
        ),
    ]

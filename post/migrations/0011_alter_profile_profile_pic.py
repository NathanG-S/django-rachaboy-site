# Generated by Django 4.0.4 on 2022-11-20 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0010_alter_profile_profile_pic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_pic',
            field=models.ImageField(blank=True, default='error.gif', null=True, upload_to='profile_images'),
        ),
    ]
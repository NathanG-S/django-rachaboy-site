# Generated by Django 4.0.4 on 2022-11-16 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0009_alter_profile_profile_pic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_pic',
            field=models.ImageField(blank=True, default='media/photo.jpg', null=True, upload_to='profile_images'),
        ),
    ]

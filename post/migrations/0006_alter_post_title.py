# Generated by Django 4.0.4 on 2022-10-30 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0005_post_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=120, verbose_name='Название поста'),
        ),
    ]

from audioop import reverse
from distutils.command.upload import upload
from enum import unique
from pyexpat import model
from tabnanny import verbose
from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.urls import reverse
from slugify import slugify
from autoslug import AutoSlugField
from uuslug import uuslug
from django.contrib.auth.models import User
from ckeditor_uploader.fields import RichTextUploadingField
from taggit.managers import TaggableManager
from taggit.models import Tag

def instance_slug(instance):
    return instance.title

def slugify_value(value):
    return value.replace(' ', '-')

class Ip(models.Model):
    ip = models.CharField(max_length = 100, verbose_name = 'ip')
    def __str__(self):
        return self.ip

class Post(models.Model):
    author = models.ForeignKey(User, on_delete = models.CASCADE, verbose_name = 'Автор')
    title = models.CharField(max_length = 120, verbose_name = 'Название поста')
    content = RichTextUploadingField(blank=True, null=True)
    published = models.DateTimeField(auto_now_add = True, db_index= True, verbose_name ="Дата публикации")
    rubric = models.ForeignKey('Rubric', on_delete = models.PROTECT, verbose_name = 'Рубрика', null=True, blank=True, related_name='post')
    slug = AutoSlugField(max_length=255, unique=True, verbose_name = 'URL', null = True, blank = True, populate_from = instance_slug, slugify = slugify_value)
    favourites = models.ManyToManyField(User, related_name='favourite', default=None, blank = True)
    image = models.ImageField(upload_to = 'post_main_images', blank = True, null = True)
    description = models.TextField(max_length=1200)
    views = models.ManyToManyField(Ip, related_name = 'post_views', blank = True)
    rate = models.PositiveIntegerField(default = 0)
    tags = TaggableManager()

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ['-published']
    def __str__(self):
        return self.title or ''
    def total_views(self):
        return self.views.count()
    def get_absolute_url(self):
        return reverse('post', kwargs = {'post_slug' : self.slug})

    def save(self, *args, **kwargs):
        self.slug = uuslug(self.slug, instance=self)
        super(Post, self).save(*args, **kwargs)



class Rubric(models.Model):
    name = models.CharField(max_length = 50, db_index = True, verbose_name = 'Рубрика')
    slug = models.SlugField(max_length=255, unique=True, verbose_name = 'URL', null = True, blank = True)

    def __str__(self):
        return self.name or ''

    def get_absolute_url(self):
        return reverse('by_rubric', kwargs = {'rubric_slug' : self.slug})

    class Meta:
        verbose_name = "Рубрика"
        verbose_name_plural = 'Рубрики'
        ordering = ['name']

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete = models.CASCADE, verbose_name = 'Пост', related_name='comments')
    author = models.ForeignKey(User, on_delete = models.CASCADE, verbose_name = 'Автор')
    content = models.CharField(max_length = 250, verbose_name='Контент')
    published = models.DateTimeField(auto_now_add = True, db_index= True, verbose_name = "Дата публикации")

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-published']

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    profile_pic = models.ImageField(upload_to = 'profile_images', null = True, blank = True)
    bio = models.TextField()

    def __str__(self):
        return self.user.username or ''
        
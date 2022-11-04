from django.contrib import admin
from .models import Post, Rubric, Comment, Profile, Ip
# Register your models here.
admin.site.register(Comment)
admin.site.register(Post)
admin.site.register(Rubric)
admin.site.register(Profile)
admin.site.register(Ip)

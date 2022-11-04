from __future__ import absolute_import

from django.urls import re_path
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.urls import include, path
from ckeditor_uploader import views

urlpatterns = [
    re_path(r'^upload/', login_required(views.upload), name='ckeditor_upload'),
    re_path(r'^browse/', never_cache(login_required(views.browse)), name='ckeditor_browse'),
    path('__debug__/', include('debug_toolbar.urls')),
]
"""postsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from post.views import by_rubric, post, by_comment, PostCreateView, PostUpdateView, PostDeleteView, login_page, logout_page, register, detail_post, profile, favourite_add, favourite_list,delete_comment, get_profile,activate, about
from post.views import day_post, week_post, month_post, year_post, by_tag, to_authors, feedback
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from post import urls
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', post, name = 'main'),
    path('post/rubric/<slug:rubric_slug>', by_rubric, name = 'by_rubric'),
    path('post/tag/<int:tag_id>', by_tag, name = 'by_tag'),
    path('post/comments/<int:post_id>', by_comment, name = 'by_comment'),
    path('post/create_post', PostCreateView.as_view(), name = 'create_post'),
    path('post/update_post/<int:pk>', PostUpdateView.as_view(), name = 'update_post'),
    path('post/delete_view/<int:pk>', PostDeleteView.as_view(), name = 'delete_post'),
    path('post/login/', login_page, name = 'login'),
    path('post/register/', register, name = 'register'),
    path('post/logout/', logout_page, name = 'logout'),
    #path('post/detail_post/<int:post_id>', detail_post, name = 'detail_post'),
    path('post/<slug:post_slug>/', detail_post, name = 'post'),
    path('profile/', profile, name = 'profile'),
    path('fav/<int:id>', favourite_add, name = 'favourite_add'),
    path('profile/favourites/', favourite_list, name = 'favourite_list'),
    path('post/comments/delete/<int:comment_id>', delete_comment, name = 'delete_comment'),
    path('get_profile/<int:user_id>', get_profile, name = 'get_profile'),
    path('about/', about, name = 'about' ),
    path('to_authors/', to_authors, name = 'to_authors'),
    path('day_post/', day_post, name='day_post'),
    path('week_post/', week_post, name='week_post'),
    path('month_post/', month_post, name='month_post'),
    path('year_post/', year_post, name='year_post'),
    path('feedback/', feedback, name='feedback'),
    path('activate/<uidb64>/<token>/',
        activate, name='activate'),
    path('reset_password/', auth_views.PasswordResetView.as_view(), name = 'reset_password'),

    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name = 'password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name = 'password_reset_confirm'),

    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name = 'password_reset_complete'),

    path('ckeditor/', include(urls)),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

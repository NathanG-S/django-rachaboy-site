
from calendar import month
from datetime import datetime, timedelta
from email import message
from django import views
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, HttpResponseRedirect
from requests import request
from .models import Post, Profile, Rubric, Comment, Ip
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import PostForm, CreateUserForm, CommentForm, UpdateProfileForm, UpdateUserForm, feedbackform
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .filters import PostFilter, TagFilter
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from django.db.models import Count
from taggit.models import Tag


#Вывод всех постов на главную страницу
def post(request):
    posts = Post.objects.select_related('rubric').all()
    rubrics = Rubric.objects.all()
    
    myFilter = PostFilter(request.GET, queryset=posts)
    posts = myFilter.qs

    context = {
    'posts' : posts, 
    'rubrics' : rubrics,
    'myFilter' : myFilter,
    
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posts')]
    related_posts = sorted(related_posts)[::-1][:6]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post
   
    return render(request, 'post/main.html', context)

# Метод для получения айпи
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR') # В REMOTE_ADDR значение айпи пользователя

    return ip


#Вывод одного поста детально
def detail_post(request, post_slug):
    post = Post.objects.get(slug = post_slug)
    posts = Post.objects.prefetch_related('views')
    fav = bool
    if post.favourites.filter(id=request.user.id).exists():
        fav = True
    rubrics = Rubric.objects.all()
    ip = get_client_ip(request)

    if Ip.objects.filter(ip=ip).exists():
        post.views.add(Ip.objects.get(ip=ip))
    else:
        Ip.objects.create(ip=ip)
        post.views.add(Ip.objects.get(ip=ip))

    context = {
        'post' : post,
        'posts' : posts,
        'rubrics' : rubrics,
        'fav' : fav,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posts')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.filter(title__in = related_lst)
    context['related_posts'] = related_post
    return render(request, 'post/detail_post.html', context)

#Вывод постов по рубрикам
def by_rubric(request, rubric_slug):
    all_posts = Post.objects.all()
    rubrics = Rubric.objects.all()
    current_rubric =  Rubric.objects.get(slug=rubric_slug)
    posts = current_rubric.post.all()
    
    myFilter = PostFilter(request.GET, queryset=posts)
    posts = myFilter.qs
    context = {
        'all_posts' : all_posts,
        'posts' : posts,
        'rubrics' : rubrics,
        'current_rubric' : current_rubric,
        'myFilter' : myFilter
    }
    related_posts = [(i.views.count(), i.title) for i in context.get('all_posts')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.filter(title__in = related_lst)
    context['related_posts'] = related_post
    return render(request, 'post/by_rubric.html', context)

#Вывод постов по тегам
def by_tag(request, tag_id):
    tags = Tag.objects.all()
    all_posts = Post.objects.all()
    current_tag = Tag.objects.get(id = tag_id)
    
    posts = Post.objects.filter(tags=current_tag)
    posts_by_views = Post.objects.filter(tags = current_tag).annotate(total=Count('views')).order_by('-total')

    rubrics = Rubric.objects.all()
    tag_filter = TagFilter(request.GET, queryset=all_posts)

    all_posts = tag_filter.qs
    all_posts_by_views = all_posts.annotate(total=Count('views')).order_by('-total')

    tag = request.GET.get('tag')
    myFilter = PostFilter(request.GET, queryset=posts)
    posts = myFilter.qs
    
    context = {
        'posts_by_views' : posts_by_views,
        'all_posts_by_views' : all_posts_by_views,
        'all_posts':all_posts,
        'tag':tag,
        'tag_filter':tag_filter,
        'posts' : posts,
        'tags': tags,
        'current_tag' : current_tag,
        'rubrics' : rubrics,
        'myFilter' : myFilter,
        
    }
    
   
    return render(request,'post/by_tag.html', context)

#Вывод постов по тегам(по количеству просмотров)
def by_tag_view(request, tag_id):
    tags = Post.objects.all()
    all_posts = Tag.objects.all()
    current_tag = Tag.objects.get(id = tag_id)
    posts = Post.objects.filter(tags = current_tag).annotate(total=Count('views')).order_by('-total')
    rubrics = Rubric.objects.all()


#Вывод комментариев к посту
def by_comment(request, post_id):
    posts = Post.objects.all()
    post = Post.objects.select_related('rubric').get(pk = post_id)
    rubrics = Rubric.objects.all()
    
    context = {
        'posts':posts,
        'post' : post,
        'rubrics' : rubrics,
    }
    related_posts = [(i.views.count(), i.title) for i in context.get('posts')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/by_comment.html', context)


#Создание постов
class PostCreateView(LoginRequiredMixin,CreateView):
    login_url = '/login/'
    model = Post
    form_class = PostForm
    template_name = 'post/post_create.html'
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rubrics'] = Rubric.objects.all()
        return context
        
    def form_valid(self, form):
        #Разграничение прав для ReadOnly
        if not self.request.user.groups.filter(name='ReadOnly').exists():
            self.object = form.save(commit=False)
            if 'image' in self.request.FILES:
                self.object.image = self.request.FILES['image']
            self.object.author = self.request.user
            self.object.slug = self.object.title
            self.object.save()
            form.save_m2m()
        return super().form_valid(form)
        
#Редактирование постов
class PostUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/login/'
    model = Post
    form_class = PostForm
    success_url = '/'
    #Разграничение прав для ReadOnly
    def form_valid(self, form):
        if not self.request.user.groups.filter(name='ReadOnly').exists():
            return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rubrics'] = Rubric.objects.all()
        return context
#Удаление постов 
class PostDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/login/'
    model = Post
    success_url = '/'
    template_name = 'post/post_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = Post.objects.all()
        context['rubrics'] = Rubric.objects.all()
        return context
        
#Регистрация пользователей 
def register(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Активируйте свой аккаунт.'
            message = render_to_string('accounts/acc_activate_email.html', {
                'user' : user,
                'domain' : current_site.domain,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            return render(request, 'accounts/activate_confirm.html', {'user' : user})
    else:
        form = CreateUserForm()

    context = {'form' : form}
    return render(request, 'accounts/register.html', context)

#Активация аккаунта после регистрации 
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk = uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('main')
    else:
        return HttpResponse('Ошибка')

#Техническая поддержка 
@login_required(login_url='login')
def feedback(request):
    rubrics = Rubric.objects.all()
    if request.method == 'POST':
        form = feedbackform(request.POST)
        if form.is_valid():
            mail_subject = form.cleaned_data.get('email')
            message = form.cleaned_data.get('text') +'(Сообщение от '+ str(request.user) + ')'
            email = EmailMessage(mail_subject, message, to=['natan.gadzaev87@gmail.com'])
            email.send()
            return redirect('main')
    else:
        form = feedbackform()
    context = {'form' : form, 'rubrics' : rubrics,}
    return render(request, 'accounts/feedback.html', context)



#Авторизация пользователей
def login_page(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            return redirect('main')
        else:
            context = {}
            messages.info(request, "Имя или пароль неверны")
            return render(request, 'accounts/login.html', context)
    context = {}
    return render(request, 'accounts/login.html', context)

#Выход с аккаунта
def logout_page(request):
    logout(request)
    return redirect('main')

#Профиль
@login_required(login_url='login')
def profile(request):
    posts = Post.objects.filter(author = request.user)
    rubrics = Rubric.objects.all()
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(request, 'accounts/profile.html',  {'user_form': user_form, 'profile_form': profile_form, 'posts' : posts, 'rubrics' : rubrics,})
#Профиль другого юзера
def get_profile(request, user_id):
    user = User.objects.get(id = user_id)
    profile = Profile.objects.get(user = user)
    posts = Post.objects.filter(author = user)
    rubrics = Rubric.objects.all()
    context = {
        'user' : user,
        'posts' : posts,
        'rubrics' : rubrics,
        'profile' : profile,
    }
    return render(request, 'accounts/get_profile.html', context)

#Добавление в избранное 
@login_required(login_url='login')
def favourite_add(request, id):
    post = get_object_or_404(Post, id = id)
    if post.favourites.filter(id=request.user.id).exists():
        post.favourites.remove(request.user)
        
        #return redirect('favourite_list')
    else:
        post.favourites.add(request.user)
        
    return HttpResponseRedirect(request.META['HTTP_REFERER'])
    #return redirect('favourite_list')

#Список избранных постов
@login_required(login_url='login')
def favourite_list(request):
    rubrics = Rubric.objects.all()
    new = Post.objects.filter(favourites=request.user)
    myFilter = PostFilter(request.GET, queryset=new)
    new = myFilter.qs
    context = {
        'new' : new,
        'rubrics' : rubrics,
        'myFilter' : myFilter,
    }
    return render(request, 'accounts/favourites.html', context)

#Удаление комментов
def delete_comment(request, comment_id):
    comment = Comment.objects.get(id = comment_id)
    comment.delete()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])
    
#Устройство сайта
def about(request):
    rubrics = Rubric.objects.all()
    context = {
        'rubrics' : rubrics,
    }
    return render(request, 'post/about.html', context)

#Лучшие публикации за сутки
def day_post(request):
    posted = Post.objects.all()
    now = datetime.now() - timedelta(hours=24)
    day_posts = Post.objects.filter(published__gte = now)
    rubrics = Rubric.objects.all()
    posts = Post.objects.annotate(total=Count('views')).order_by('-total')
    context = {
    'posts' : posts,
    'posted':posted,
    'day_posts' : day_posts,
    'rubrics' : rubrics,
    }



    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post
    
    return render(request, 'post/day_post.html', context)

#Лучшие публикации за неделю
def week_post(request):
    posted = Post.objects.all()
    now = datetime.now() - timedelta(hours=24*7)
    day_posts = Post.objects.filter(published__gte = now)
    rubrics = Rubric.objects.all()
    posts = Post.objects.annotate(total=Count('views')).order_by('-total')
    context = {
    'posts' : posts,
    'posted':posted,
    'day_posts' : day_posts,
    'rubrics' : rubrics,
    }


    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/week_post.html', context)

#Лучшие публикации за месяц
def month_post(request):
    posted = Post.objects.all()
    now = datetime.now() - timedelta(hours=24*30)
    day_posts = Post.objects.filter(published__gte = now)
    rubrics = Rubric.objects.all()
    posts = Post.objects.annotate(total=Count('views')).order_by('-total')
    context = {
    'posts' : posts,
    'posted':posted,
    'day_posts' : day_posts,
    'rubrics' : rubrics,
    }


    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/month_post.html', context)

#Лучшие публикации за год
def year_post(request):
    
    posted = Post.objects.all()
    now = datetime.now() - timedelta(hours=24*30*12)
    day_posts = Post.objects.filter(published__gte = now)
    rubrics = Rubric.objects.all()
    posts = Post.objects.annotate(total=Count('views')).order_by('-total')
    context = {
    'posts' : posts,
    'posted':posted,
    'day_posts' : day_posts,
    'rubrics' : rubrics,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/year_post.html', context)

#Для авторов
def to_authors(request):
    rubrics = Rubric.objects.all()
    context = {
        'rubrics' : rubrics,
    }
    return render(request, 'post/to_authors.html', context)





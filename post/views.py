from calendar import month
from datetime import datetime, timedelta
from email import message
from django import views
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, HttpResponseRedirect
from requests import request
from .models import Post, Profile, Rubric, Comment, Ip
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import PostForm, CreateUserForm, UpdateProfileForm, UpdateUserForm, feedbackform
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
from django.db.models import Count, Sum
from taggit.models import Tag, TaggedItem
from django.core.cache import cache
from django.core.paginator import Paginator


#Вывод всех постов на главную страницу(optimized 149 --> 10)
def post(request):
    cache.delete('current_tag')
    
    #now = datetime.now() - timedelta(hours=24*7)
    posts = Post.objects.select_related('rubric', 'author__profile', ).prefetch_related('rates_plus', 'rates_minus', 'views', 'favourites').annotate(count = Count('views')).order_by('-published')
    rubrics = Rubric.objects.all()
    best_posts = Post.objects.prefetch_related('rates_plus', 'rates_minus', 'views')\
    .annotate(total =  Count('rates_plus', distinct=True) - Count('rates_minus', distinct=True)).order_by('-total')[:3]
    
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    
    page_obj = paginator.get_page(page_number)
   
    myFilter = PostFilter(request.GET, queryset=posts)
    posts = myFilter.qs
    
    context = {
    'page_obj' : page_obj,
    'best_posts' : best_posts,
    'posts' : posts, 
    'rubrics' : rubrics,
    'myFilter' : myFilter,
    
    }

    related_posts = [(i.count, i.title) for i in context.get('posts')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post
    
    return render(request, 'post/main.html', context)

#Поиск по постам 
def search_post(request):
    all_posts = Post.objects.select_related('rubric', 'author__profile').prefetch_related('rates_plus', 'rates_minus', 'views').all()
    rubrics = Rubric.objects.all()
    myFilter = PostFilter(request.GET, queryset=all_posts)
    posts = myFilter.qs

    context = {
        'posts' : posts,
        'rubrics' : rubrics,
        'myFilter' : myFilter,
    }

    return render(request, 'post/search_post.html', context)


# Метод для получения айпи
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR') # В REMOTE_ADDR значение айпи пользователя

    return ip


#Вывод одного поста детально(optimized)
def detail_post(request, post_slug):
    post = Post.objects.select_related('rubric','author__profile')\
    .prefetch_related('rates_plus', 'rates_minus')\
    .get(slug = post_slug)

    popular = Post.objects.filter(rubric = post.rubric).exclude(title = post.title)\
        .select_related('rubric', 'author__profile').prefetch_related('rates_plus', 'rates_minus', 'views', 'favourites')\
            .annotate(total = Count('rates_plus', distinct=True) - Count('rates_minus', distinct=True)).order_by('-total')[:3]

    posts = Post.objects.prefetch_related('views').all()
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
        'popular' : popular,
        'post' : post,
        'posts' : posts,
        'rubrics' : rubrics,
        'fav' : fav,
    }
    
    related_posts = [(i.views.count(), i.title) for i in context.get('posts')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    
    context['related_posts'] = related_post
    return render(request, 'post/detail_post.html', context)

#Вывод постов по рубрикам(optimized)
def by_rubric(request, rubric_slug):
    best_posts = Post.objects.prefetch_related('rates_plus', 'rates_minus', 'views')\
    .annotate(total =  Count('rates_plus', distinct=True) - Count('rates_minus', distinct=True)).order_by('-total')[:3]
    all_posts = Post.objects.prefetch_related('views').all()
    rubrics = Rubric.objects.all()
    current_rubric =  Rubric.objects.get(slug=rubric_slug)
    cache.set('current_rubric', current_rubric)
    posts = current_rubric.post.select_related('rubric', 'author__profile').prefetch_related('rates_plus','rates_minus','views', 'favourites').all() 

    myFilter = PostFilter(request.GET, queryset=posts)
    posts = myFilter.qs

    context = {
        'best_posts' : best_posts,
        'all_posts' : all_posts,    
        'posts' : posts,
        'rubrics' : rubrics,
        'current_rubric' : current_rubric,
        'myFilter' : myFilter
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('all_posts')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post
    return render(request, 'post/by_rubric.html', context)

#Вывод постов по тегам(optimized)
def by_tag(request, tag_id):
    tags = Tag.objects.all()
    all_posts = Post.objects.select_related('rubric', 'author__profile').prefetch_related('rates_plus', 'rates_minus', 'views', 'favourites').all()
    current_tag = Tag.objects.get(id = tag_id)

    best_posts = Post.objects.prefetch_related('rates_plus', 'rates_minus', 'views')\
    .annotate(total =  Count('rates_plus', distinct=True) - Count('rates_minus', distinct=True)).order_by('-total')[:3]

    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views').filter(tags=current_tag)

    rubrics = Rubric.objects.all()
    tag_filter = TagFilter(request.GET, queryset=all_posts)
    all_posts = tag_filter.qs   
    tag = request.GET.get('tag')
    
    if tag != None:
        if Tag.objects.filter(name = tag).exists():
            tag = Tag.objects.get(name = tag)
            cache.set('current_tag', tag)
        else:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
        
    else:
        cache.set('current_tag', current_tag)

    myFilter = PostFilter(request.GET, queryset=posts)
    posts = myFilter.qs
    
    context = {
        'best_posts' : best_posts,
        'all_posts':all_posts,
        'tag':tag,
        'tag_filter':tag_filter,
        'posts' : posts,
        'tags': tags,
        'current_tag' : current_tag,
        'rubrics' : rubrics,
        'myFilter' : myFilter,

    }
    related_posts = [(i.views.count(), i.title) for i in context.get('posts')]
    related_posts = sorted(related_posts)[::-1][:6]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request,'post/by_tag.html', context)

#Вывод постов по тегам(по количеству просмотров)(optimized)
def by_tag_view(request):
    current_tag = cache.get('current_tag')
    
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views')\
            .filter(tags = current_tag).annotate(total=Count('views')).order_by('-total')

    rubrics = Rubric.objects.all()
    context = {
        'current_tag' : current_tag,
        'posts' : posts,
        'rubrics' : rubrics
    }
    related_posts = [(i.views.count(), i.title) for i in context.get('posts')]
    related_posts = sorted(related_posts)[::-1][:6]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post
    #cache.delete('current_tag')
    return render(request, 'post/by_tag_view.html', context)

#Вывод постов по рейтингу(релевантности)(optimized)
def by_tag_rate(request):
    current_tag = cache.get('current_tag')

    posts = Post.objects.select_related('rubric', 'author__profile').prefetch_related('rates_plus', 'rates_minus', 'views')\
        .filter(tags = current_tag).annotate(total = Count('rates_plus', distinct=True) - Count('rates_minus', distinct=True))\
            .order_by('-total')

    rubrics = Rubric.objects.all()
    context = {
        'current_tag' : current_tag,
        'posts' : posts,
        'rubrics' : rubrics,
    }
    related_posts = [(i.views.count(), i.title) for i in context.get('posts')]
    related_posts = sorted(related_posts)[::-1][:6]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post
    return render(request, 'post/by_tag_rate.html', context)

#Вывод комментариев к посту
def by_comment(request, post_id):
    
    posts = Post.objects.prefetch_related('views').all()
    post = Post.objects.select_related('rubric', 'author__profile').prefetch_related('rates_plus', 'rates_minus').get(pk = post_id)
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
        else:
            return render(self.request,'accounts/readonly.html')
        
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
        else:
            return render(self.request,'accounts/readonly.html')
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
        context['post'] = Post.objects.get(id = self.object.id)
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
            #messages.success(request, f'Аккаунт с именем {user} был создан')
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

#Профиль(optimized)
@login_required(login_url='login')
def profile(request):
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus','rates_minus','views').filter(author = request.user)

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
    user = User.objects.select_related('profile').get(id = user_id)
    
    profile = Profile.objects.get(user = user)
    posts = Post.objects.select_related('rubric', 'author__profile').prefetch_related('rates_plus', 'rates_minus', 'views').filter(author = user)
    rubrics = Rubric.objects.all()
    if profile.followers.filter(id=request.user.id).exists():
        is_follower = True
    else:
        is_follower = False
    context = {
        'is_follower' : is_follower,
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

#Подписка на пользователя
@login_required(login_url='login')
def follow_user(request, id):
    
    profile = get_object_or_404(Profile, id=id)
    if profile.followers.filter(id=request.user.id).exists():
        profile.followers.remove(request.user)
        
    else:
        profile.followers.add(request.user)
        #cache.set('is_follower', True)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

#Добавление в плюс рейтинг
@login_required(login_url='login')
def add_rate_plus(request, id):
    if not request.user.groups.filter(name='ReadOnly').exists():
        post = get_object_or_404(Post, id=id)
        if post.rates_plus.filter(id=request.user.id).exists():
            post.rates_plus.remove(request.user)
        elif post.rates_minus.filter(id=request.user.id).exists():
            post.rates_minus.remove(request.user)
            post.rates_plus.add(request.user)
        else:
            post.rates_plus.add(request.user)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return render(request,'accounts/readonly.html')

#Добавление в минус рейтинг
@login_required(login_url='login') 
def add_rate_minus(request, id):
    if not request.user.groups.filter(name='ReadOnly').exists():
        post = get_object_or_404(Post, id=id)
        if post.rates_minus.filter(id=request.user.id).exists():
            post.rates_minus.remove(request.user)
        elif post.rates_plus.filter(id=request.user.id).exists():
            post.rates_plus.remove(request.user)
            post.rates_minus.add(request.user)
        else:
            post.rates_minus.add(request.user)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return render(request,'accounts/readonly.html')

#Список избранных постов
@login_required(login_url='login')
def favourite_list(request):
    rubrics = Rubric.objects.all()
    new = Post.objects.select_related('rubric', 'author__profile').prefetch_related('rates_plus', 'rates_minus', 'views', 'favourites').filter(favourites=request.user)
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
    posted = Post.objects.prefetch_related('views').all()
    now = datetime.now() - timedelta(hours=24)
    rubrics = Rubric.objects.all()
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views')\
            .filter(published__gte = now).annotate(total=Count('views')).order_by('-total')

    context = {
    'posted' : posted,
    'posts' : posts,
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
    posted = Post.objects.prefetch_related('views').all()
    now = datetime.now() - timedelta(hours=24*7)
    rubrics = Rubric.objects.all()
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views')\
            .filter(published__gte = now).annotate(total=Count('views')).order_by('-total')

    context = {
    'posted' : posted,
    'posts' : posts,
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
    posted = Post.objects.prefetch_related('views').all()
    now = datetime.now() - timedelta(hours=24*30)
    rubrics = Rubric.objects.all()
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views')\
            .filter(published__gte = now).annotate(total=Count('views')).order_by('-total')

    context = {
    'posted' : posted,   
    'posts' : posts,
    'rubrics' : rubrics,
    }


    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/month_post.html', context)
#83
#Лучшие публикации за год
def year_post(request):
    posted = Post.objects.prefetch_related('views').all()
    now = datetime.now() - timedelta(hours=24*30*12)
    rubrics = Rubric.objects.all()
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views')\
            .filter(published__gte = now).annotate(total=Count('views')).order_by('-total')

    context = {
    'posted' : posted,    
    'posts' : posts,
    'rubrics' : rubrics,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/year_post.html', context)


 

#Публикации с рейтингом >= 0
def rate_more_zero(request):
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views', 'favourites')\
            .annotate(total = Count('rates_plus', distinct=True) - Count('rates_minus', distinct=True)).filter(total__gte = 0).order_by('-published')

    posted = Post.objects.prefetch_related('views').all()
    rubrics = Rubric.objects.all()

    context = {
        'posts' : posts,
        'posted' : posted,
        'rubrics' : rubrics,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/rate_more_zero.html', context)

#Публикации с рейтингом >= 20
def rate_more_twenty(request):
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views', 'favourites')\
            .annotate(total = Count('rates_plus', distinct=True) - Count('rates_minus', distinct=True)).filter(total__gte = 20).order_by('-published')
    posted = Post.objects.prefetch_related('views').all()
    rubrics = Rubric.objects.all()

    context = {
        'posts' : posts,
        'posted' : posted,
        'rubrics' : rubrics,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/rate_more_twenty.html', context)


#Публикации с рейтнгом >= 50
def rate_more_fifty(request):
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views', 'favourites')\
            .annotate(total = Count('rates_plus', distinct=True) - Count('rates_minus', distinct=True)).filter(total__gte = 50).order_by('-published')
    posted = Post.objects.prefetch_related('views').all()
    rubrics = Rubric.objects.all()

    context = {
        'posts' : posts,
        'posted' : posted,
        'rubrics' : rubrics,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/rate_more_fifty.html', context)

#Публикации с рейтнгом >= 100
def rate_more_hundreed(request):
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views', 'favourites')\
            .annotate(total = Count('rates_plus', distinct=True) - Count('rates_minus', distinct=True)).filter(total__gte = 100).order_by('-published')
    posted = Post.objects.prefetch_related('views').all()
    rubrics = Rubric.objects.all()

    context = {
        'posts' : posts,
        'posted' : posted,
        'rubrics' : rubrics,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/rate_more_hundreed.html', context)


#Лучшие посты за сутки в конкретной категории
def day_post_rubric(request):
    current_rubric = cache.get('current_rubric')
    posted = Post.objects.prefetch_related('views').all()
    now = datetime.now() - timedelta(hours=24)
    rubrics = Rubric.objects.all()
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views')\
            .filter(published__gte = now).filter(rubric = current_rubric).annotate(total=Count('views')).order_by('-total')

    context = {
    'posted' : posted,
    'posts' : posts,
    'rubrics' : rubrics,
    'current_rubric' : current_rubric,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post
    
    return render(request, 'post/day_post_rubric.html', context)

#Лучшие посты за неделю в конкретной категории

def week_post_rubric(request):
    current_rubric = cache.get('current_rubric')
    posted = Post.objects.prefetch_related('views').all()
    now = datetime.now() - timedelta(hours=24*7)
    rubrics = Rubric.objects.all()
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views')\
            .filter(published__gte = now).filter(rubric = current_rubric).annotate(total=Count('views')).order_by('-total')

    context = {
    'posted' : posted,
    'posts' : posts,
    'rubrics' : rubrics,
    'current_rubric' : current_rubric,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/week_post_rubric.html', context)

#Лучшие публикации за месяц
def month_post_rubric(request):
    current_rubric = cache.get('current_rubric')
    posted = Post.objects.prefetch_related('views').all()
    now = datetime.now() - timedelta(hours=24*30)
    rubrics = Rubric.objects.all()
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views')\
            .filter(published__gte = now).filter(rubric = current_rubric).annotate(total=Count('views')).order_by('-total')

    context = {
    'posted' : posted,   
    'posts' : posts,
    'rubrics' : rubrics,
    'current_rubric' : current_rubric,
    }


    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/month_post_rubric.html', context)
#83
#Лучшие публикации за год
def year_post_rubric(request):
    current_rubric = cache.get('current_rubric')
    posted = Post.objects.prefetch_related('views').all()
    now = datetime.now() - timedelta(hours=24*30*12)
    rubrics = Rubric.objects.all()
    posts = Post.objects.select_related('rubric', 'author__profile')\
        .prefetch_related('rates_plus', 'rates_minus', 'views')\
            .filter(published__gte = now).filter(rubric = current_rubric).annotate(total=Count('views')).order_by('-total')

    context = {
    'posted' : posted,    
    'posts' : posts,
    'rubrics' : rubrics,
    'current_rubric' : current_rubric,
    }

    related_posts = [(i.views.count(), i.title) for i in context.get('posted')]
    related_posts = sorted(related_posts)[::-1][:4]
    related_lst = [y for x in related_posts for y in x if type(y) == str]
    related_post = Post.objects.prefetch_related('views').filter(title__in = related_lst)
    context['related_posts'] = related_post

    return render(request, 'post/year_post_rubric.html', context)






#Для авторов
def to_authors(request):
    rubrics = Rubric.objects.all()
    context = {
        'rubrics' : rubrics,
    }
    return render(request, 'post/to_authors.html', context)



def privacy(request):
    rubrics = Rubric.objects.all()
    context = {
        'rubrics' : rubrics,
    }
    return render(request, 'accounts/privacy.html', context)

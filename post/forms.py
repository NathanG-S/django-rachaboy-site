from importlib.metadata import requires
from django import forms
from django.forms import CharField, ModelForm
from .models import Post, Comment, Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'content', 'rubric', 'tags','image', 'description')
        labels = {
            'rubric' : ('Категория'),
            'content' : ('Содержание'),
            'title' : ('Название'),
            'tags': ('Теги'),
            'image' : ('Изображение поста на главной странице'),
            'description' : ('Содержание поста на главной странице'),
        }

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def clean(self):
        clean_data = super(CreateUserForm, self).clean()
        email = clean_data.get('email')
        username = clean_data.get('username')
        if not email:
            raise forms.ValidationError(('Введите e-mail'), code = 'email')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError(u'Пользователь с таким e-mail уже существует.')
            
        

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('content', )
        widgets = {
            'content' : forms.TextInput(attrs={'placeholder' : 'Добавить комментарий',})
        }
        labels = {
            'content' : ('')
        }


class UpdateUserForm(forms.ModelForm):
    username = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email']


class UpdateProfileForm(forms.ModelForm):
    profile_pic = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control-file'}))
    bio = forms.CharField(max_length=255,widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))
    git_href = forms.URLField(max_length=200, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    class Meta:
        model = Profile
        fields = ['profile_pic', 'bio', 'git_href',]

class feedbackform(forms.Form):
    email = forms.EmailField(required=True,
                             widget=forms.TextInput(attrs={'class': 'form-control'}))
    text = forms.CharField( widget=forms.Textarea(attrs={'class': 'form-control'}))


from cProfile import label
from dataclasses import field
from logging import Filter
from tkinter import Widget
from turtle import width
import django_filters
from .models import *
from django_filters import CharFilter
from django.forms.widgets import TextInput

class PostFilter(django_filters.FilterSet):
    title = CharFilter(field_name='title', lookup_expr='icontains', widget=TextInput(attrs={'placeholder': 'Search...'}))
    class Meta:
        model = Post
        fields = ('title',)
        widgets = {
            
        }

class TagFilter(django_filters.FilterSet):
    tag = CharFilter(field_name='tags__name', lookup_expr='iexact', widget=TextInput(attrs={'placeholder': 'Search tag...'}))
    class Meta:
        model = Post
        fields = ['tag',]
        filter_overrides = {
            TaggableManager: {'filter_class': CharFilter },
        }
        widgets = {
           
        }
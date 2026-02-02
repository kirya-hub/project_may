from django.urls import path
from .views import cafe_detail, category_detail

urlpatterns = [
    path('<slug:slug>/', cafe_detail, name='cafe_detail'),
    path('<slug:slug>/category/<slug:category_slug>/', category_detail, name='category_detail'),
]

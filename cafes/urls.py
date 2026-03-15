from django.urls import path

from .views import cafe_detail, cafe_edit, cafes_list, category_detail

urlpatterns = [
    path('', cafes_list, name='cafes_list'),
    path('<slug:slug>/', cafe_detail, name='cafe_detail'),
    path('<slug:slug>/edit/', cafe_edit, name='cafe_edit'),
    path(
        '<slug:slug>/category/<slug:category_slug>/',
        category_detail,
        name='category_detail',
    ),
]

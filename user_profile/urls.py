from django.urls import path
from . import views

urlpatterns = [
    path('<str:username>/', views.profile_detail, name='profile_by_username'),
    path('id/<int:user_id>/', views.profile_detail, name='profile_by_id'),
]

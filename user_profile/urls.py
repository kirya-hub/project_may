from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_home, name='profile_home'),
    path('me/', views.my_profile, name='my_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('id/<int:user_id>/', views.profile_detail, name='profile_by_id'),
    path('<str:username>/', views.profile_detail, name='profile_by_username'),
]

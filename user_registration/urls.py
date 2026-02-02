from django.urls import path
from .views import AuthLoginView, AuthRegisterView, AuthLogoutView

urlpatterns = [
    path('login/', AuthLoginView.as_view(), name='login'),
    path('register/', AuthRegisterView.as_view(), name='register'),
    path('logout/', AuthLogoutView.as_view(), name='logout'),
]

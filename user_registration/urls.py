from django.urls import path

from .views import AuthLoginView, AuthLogoutView, AuthRegisterView, ConfirmEmailView, EmailSentView

urlpatterns = [
    path('login/', AuthLoginView.as_view(), name='login'),
    path('register/', AuthRegisterView.as_view(), name='register'),
    path('logout/', AuthLogoutView.as_view(), name='logout'),
    path('confirm/<uuid:token>/', ConfirmEmailView.as_view(), name='confirm_email'),
    path('email-sent/', EmailSentView.as_view(), name='email_sent'),
]

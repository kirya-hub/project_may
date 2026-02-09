from django.urls import path
from . import views

app_name = "friends"

urlpatterns = [
    path("", views.friends_page, name="friends_page"),
    path("toggle/<int:user_id>/", views.follow_toggle, name="follow_toggle"),
]

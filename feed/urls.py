from django.urls import path

from .views import feed_home, toggle_like

urlpatterns = [
    path('', feed_home, name='home'),
    path('like/<int:order_id>/', toggle_like, name='toggle_like'),
]

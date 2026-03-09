from django.urls import path

from .views import add_comment, delete_comment, feed_home, toggle_like

urlpatterns = [
    path('', feed_home, name='home'),
    path('like/<int:order_id>/', toggle_like, name='toggle_like'),
    path('comment/<int:order_id>/', add_comment, name='add_comment'),
    path('comment/delete/<int:comment_id>/', delete_comment, name='delete_comment'),
]

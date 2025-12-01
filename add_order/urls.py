from django.urls import path
from . import views

urlpatterns = [
    path('', views.add_order_page, name='add_order'),
]

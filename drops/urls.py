from django.urls import path

from . import views

app_name = 'drops'

urlpatterns = [
    path('', views.drops_page, name='drops_page'),
    path('choose/<int:option_id>/', views.choose_drop, name='choose_drop'),
]

from django.urls import path

from . import views

app_name = 'drops'

urlpatterns = [
    path('', views.drops_page, name='drops_page'),
    path('grab/', views.grab, name='grab'),
    path('info/', views.drops_info, name='drops_info'),
    path('choose/<int:option_id>/', views.choose_drop, name='choose_drop'),
]

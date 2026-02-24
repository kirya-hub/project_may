from django.urls import path

from . import views

app_name = 'trades'

urlpatterns = [
    path('', views.trade_home, name='home'),
    path('new/<str:username>/', views.trade_new, name='new'),
    path('<int:trade_id>/', views.trade_detail, name='detail'),
    path('<int:trade_id>/accept/', views.trade_accept, name='accept'),
    path('<int:trade_id>/decline/', views.trade_decline, name='decline'),
    path('<int:trade_id>/cancel/', views.trade_cancel, name='cancel'),
    path('activity/', views.trade_activity, name='activity'),
]

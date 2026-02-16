from django.urls import path

from . import views

app_name = 'promo'

urlpatterns = [
    path('', views.promo_home, name='home'),
    path('shop/', views.coupon_shop, name='shop'),
    path('shop/buy/<int:offer_id>/', views.buy_coupon, name='buy_coupon'),
    path('coupons/', views.my_coupons, name='my_coupons'),
    path('coupons/use/<int:coupon_id>/', views.use_coupon, name='use_coupon'),
]

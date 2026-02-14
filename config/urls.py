from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('feed.urls')),
    path('', include('user_registration.urls')),
    path('profile/', include('user_profile.urls')),
    path('add/', include('add_order.urls')),
    path('cafes/', include('cafes.urls')),
    path('friends/', include('friends.urls')),
    path('promo/', include('promo.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

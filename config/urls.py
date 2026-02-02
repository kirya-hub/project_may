from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user_registration.urls')),
    path('profile/', include('user_profile.urls')),
    path('add/', include('add_order.urls')),
    path('cafes/', include('cafes.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('admin/', include('material.admin.urls')), #custom admin file
    path('api/', include('elections.urls')),  # API endpoints
    path('', include('elections.urls')),      # Web interface URLs
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 
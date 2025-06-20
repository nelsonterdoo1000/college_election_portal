from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('elections.urls')),  # API endpoints
    path('', include('elections.urls')),      # Web interface URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
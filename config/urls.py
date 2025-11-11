from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from usuarios.views import login_view

urlpatterns = [
    path('', login_view, name='home'),
    path('', include('usuarios.urls')),

    path('admin/', admin.site.urls),

    # API
    path('api/usuarios/', include('usuarios.urls')),
    path('api/denuncias/', include('denuncias.urls')),
]

# Servir archivos estáticos en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

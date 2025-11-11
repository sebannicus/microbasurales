from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from usuarios.views import home_ciudadano_view, login_view

urlpatterns = [
    path('', login_view, name='login'),
    path('home/', home_ciudadano_view, name='home_ciudadano'),
    path('', include('usuarios.urls')),

    path('admin/', admin.site.urls),

    # API
    path('api/usuarios/', include('usuarios.urls')),
    path('api/denuncias/', include('denuncias.urls')),
]

# Servir archivos estáticos en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

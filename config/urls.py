from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from denuncias.views import (
    panel_cuadrilla,
    panel_denuncias_alias,
    panel_fiscalizador_activos,
    panel_fiscalizador_finalizados,
)
from usuarios.views import home_ciudadano_view, login_view

urlpatterns = [
    path('', login_view, name='login'),
    path('home/', home_ciudadano_view, name='home_ciudadano'),
    path('', include('usuarios.urls')),
    path('panel/denuncias/', panel_denuncias_alias, name='panel_denuncias'),
    path('panel/denuncias/activos/', panel_fiscalizador_activos, name='panel_fiscalizador_activos'),
    path('panel/denuncias/finalizados/', panel_fiscalizador_finalizados, name='panel_fiscalizador_finalizados'),
    path('panel/cuadrilla/', panel_cuadrilla, name='panel_cuadrilla'),
    path('panel/analitica/', include(('analitica.urls', 'analitica'), namespace='analitica')),

    path('admin/', admin.site.urls),

    # API
    path('api/usuarios/', include('usuarios.urls')),
    path('api/denuncias/', include('denuncias.urls')),
]

# Servir archivos estáticos en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

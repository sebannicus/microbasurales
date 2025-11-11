from django.urls import path
from .views import (
    CrearDenunciaView,
    ListarDenunciasView,
    DenunciaDetalleView,
    CambiarEstadoView,
)

urlpatterns = [
    path('', ListarDenunciasView.as_view(), name='listar_denuncias'),
    path('crear/', CrearDenunciaView.as_view(), name='crear_denuncia'),
    path('<int:pk>/', DenunciaDetalleView.as_view(), name='detalle_denuncia'),
    path('<int:pk>/estado/', CambiarEstadoView.as_view(), name='cambiar_estado'),
]

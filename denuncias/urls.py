from django.urls import path

from .views import (
    DenunciaAdminListView,
    DenunciaAdminUpdateView,
    DenunciaListCreateView,
    MiDenunciaRetrieveUpdateView,
    MisDenunciasListView,
    MisNotificacionesListView,
    NotificacionActualizarView,
)


urlpatterns = [
    path("", DenunciaListCreateView.as_view(), name="denuncias_list_create"),
    path("mis/", MisDenunciasListView.as_view(), name="mis_denuncias"),
    path(
        "mis/<int:pk>/",
        MiDenunciaRetrieveUpdateView.as_view(),
        name="mi_denuncia_detalle",
    ),
    path("admin/", DenunciaAdminListView.as_view(), name="denuncias_admin_list"),
    path(
        "admin/<int:pk>/",
        DenunciaAdminUpdateView.as_view(),
        name="denuncias_admin_update",
    ),
    path(
        "notificaciones/",
        MisNotificacionesListView.as_view(),
        name="mis_notificaciones_denuncias",
    ),
    path(
        "notificaciones/<int:pk>/",
        NotificacionActualizarView.as_view(),
        name="notificacion_denuncia_actualizar",
    ),
]

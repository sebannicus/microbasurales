from django.urls import path

from .views import (
    DenunciaAdminListView,
    DenunciaAdminUpdateView,
    DenunciaListCreateView,
    MisDenunciasListView,
)


urlpatterns = [
    path("", DenunciaListCreateView.as_view(), name="denuncias_list_create"),
    path("mis/", MisDenunciasListView.as_view(), name="mis_denuncias"),
    path("admin/", DenunciaAdminListView.as_view(), name="denuncias_admin_list"),
    path(
        "admin/<int:pk>/",
        DenunciaAdminUpdateView.as_view(),
        name="denuncias_admin_update",
    ),
]

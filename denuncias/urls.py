from django.urls import path

from .views import DenunciaListCreateView, MisDenunciasListView


urlpatterns = [
    path("", DenunciaListCreateView.as_view(), name="denuncias_list_create"),
    path("mis/", MisDenunciasListView.as_view(), name="mis_denuncias"),
]

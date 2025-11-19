"""URLs del módulo Analítica."""

from django.urls import path

from .views import AnaliticaDashboardView, ExportarCSVView, PowerBIDatasetView

app_name = "analitica"

urlpatterns = [
    path("", AnaliticaDashboardView.as_view(), name="dashboard"),
    path("exportar-csv/", ExportarCSVView.as_view(), name="exportar_csv"),
    path("api/powerbi/", PowerBIDatasetView.as_view(), name="powerbi_api"),
]

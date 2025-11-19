"""Vistas del módulo Analítica."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from denuncias.models import Denuncia

from .services import calcular_tiempo_resolucion_horas, generar_csv_mensual


class AdministradorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe el acceso únicamente a administradores del sistema."""

    def test_func(self) -> bool:  # pragma: no cover - simple guard
        return getattr(self.request.user, "es_administrador", False)


class FuncionarioOAdministradorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Permite acceso a funcionarios municipales y administradores."""

    def test_func(self) -> bool:  # pragma: no cover - simple guard
        user = self.request.user
        es_funcionario = False
        if hasattr(user, "es_funcionario_municipal"):
            es_funcionario = user.es_funcionario_municipal()
        return getattr(user, "es_administrador", False) or es_funcionario


@dataclass
class ResumenEstado:
    estado: str
    etiqueta: str
    total: int
    porcentaje: float
    color: str


class AnaliticaDashboardView(AdministradorRequiredMixin, TemplateView):
    """Panel principal con los indicadores de la plataforma."""

    template_name = "analitica/analitica_dashboard.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        queryset = Denuncia.objects.select_related("reporte_cuadrilla").all()
        total_denuncias = queryset.count()

        estado_labels = dict(Denuncia.EstadoDenuncia.choices)
        estado_counts = {estado: 0 for estado in estado_labels.keys()}
        for entry in queryset.values("estado").annotate(total=Count("id")):
            estado_counts[entry["estado"]] = entry["total"]

        resumen_estados: List[ResumenEstado] = []
        for estado, total in estado_counts.items():
            porcentaje = round((total / total_denuncias) * 100, 2) if total_denuncias else 0.0
            resumen_estados.append(
                ResumenEstado(
                    estado=estado,
                    etiqueta=estado_labels.get(estado, estado.title()),
                    total=total,
                    porcentaje=porcentaje,
                    color=Denuncia.EstadoDenuncia.get_color(estado),
                )
            )

        denuncias_por_zona = (
            queryset.values("zona")
            .annotate(total=Count("id"))
            .order_by("-total", "zona")
        )

        con_reporte = queryset.filter(reporte_cuadrilla__isnull=False).count()
        activas = queryset.filter(
            estado__in=[
                Denuncia.EstadoDenuncia.PENDIENTE,
                Denuncia.EstadoDenuncia.EN_GESTION,
            ]
        ).count()
        finalizadas = queryset.filter(estado=Denuncia.EstadoDenuncia.FINALIZADO).count()
        zonas_monitoreadas = queryset.exclude(zona="").values("zona").distinct().count()

        promedio_delta = queryset.filter(reporte_cuadrilla__fecha_reporte__isnull=False).aggregate(
            promedio=Avg(
                ExpressionWrapper(
                    F("reporte_cuadrilla__fecha_reporte") - F("fecha_creacion"),
                    output_field=DurationField(),
                )
            )
        )["promedio"]
        tiempo_promedio_resolucion_horas = None
        tiempo_promedio_resolucion_legible = "Sin datos"
        if promedio_delta:
            horas = round(promedio_delta.total_seconds() / 3600, 2)
            tiempo_promedio_resolucion_horas = horas
            dias = round(horas / 24, 2)
            tiempo_promedio_resolucion_legible = f"{horas} h (~{dias} días)"

        context.update(
            {
                "total_denuncias": total_denuncias,
                "denuncias_por_estado": resumen_estados,
                "denuncias_por_zona": denuncias_por_zona,
                "tiempo_promedio_resolucion_horas": tiempo_promedio_resolucion_horas,
                "tiempo_promedio_resolucion_legible": tiempo_promedio_resolucion_legible,
                "denuncias_activas": activas,
                "denuncias_finalizadas": finalizadas,
                "total_con_reporte": con_reporte,
                "zonas_monitoreadas": zonas_monitoreadas,
                "tabla_resumen": [
                    {
                        "titulo": "Denuncias activas",
                        "valor": activas,
                        "detalle": "Pendientes + en gestión",
                    },
                    {
                        "titulo": "Denuncias finalizadas",
                        "valor": finalizadas,
                        "detalle": "Marcadas como finalizado",
                    },
                    {
                        "titulo": "Con reporte de cuadrilla",
                        "valor": con_reporte,
                        "detalle": "Registros con evidencia adjunta",
                    },
                    {
                        "titulo": "Zonas monitoreadas",
                        "valor": zonas_monitoreadas,
                        "detalle": "Zonas con al menos una denuncia",
                    },
                ],
                "ultimo_actualizado": timezone.localtime(timezone.now()),
                "api_url": self.request.build_absolute_uri(reverse("analitica:powerbi_api")),
            }
        )
        return context


class ExportarCSVView(FuncionarioOAdministradorRequiredMixin, TemplateView):
    """Pantalla que permite descargar el CSV mensual."""

    template_name = "analitica/exportacion_resultado.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "mes_actual": timezone.localdate().strftime("%B %Y"),
                "nombre_archivo": f"informes_microbasurales_{timezone.localdate().strftime('%m-%Y')}.csv",
            }
        )
        return context

    def get(self, request, *args: Any, **kwargs: Any):  # type: ignore[override]
        if request.GET.get("descargar"):
            return generar_csv_mensual()
        return super().get(request, *args, **kwargs)


class PowerBIDatasetView(AdministradorRequiredMixin, View):
    """Entrega un dataset completo para su consumo en Power BI."""

    def get(self, request, *args, **kwargs):  # type: ignore[override]
        queryset = (
            Denuncia.objects.select_related(
                "usuario", "reporte_cuadrilla", "reporte_cuadrilla__jefe_cuadrilla"
            )
            .all()
            .order_by("-fecha_creacion")
        )

        dataset: List[Dict[str, Any]] = []
        for denuncia in queryset:
            reporte = getattr(denuncia, "reporte_cuadrilla", None)
            fecha_resolucion = None
            if reporte and reporte.fecha_reporte:
                fecha_resolucion = timezone.localtime(reporte.fecha_reporte)

            dataset.append(
                {
                    "id": denuncia.id,
                    "fecha_creacion": timezone.localtime(denuncia.fecha_creacion).isoformat(),
                    "fecha_resolucion": fecha_resolucion.isoformat() if fecha_resolucion else None,
                    "estado": denuncia.estado,
                    "zona": denuncia.zona or "Sin zona",
                    "latitud": denuncia.latitud,
                    "longitud": denuncia.longitud,
                    "tiempo_resolucion": calcular_tiempo_resolucion_horas(denuncia),
                    "denunciante": getattr(denuncia.usuario, "username", "anónimo"),
                    "rol_que_gestiono": (
                        reporte.jefe_cuadrilla.rol if reporte and reporte.jefe_cuadrilla else None
                    ),
                    "tiene_reporte_cuadrilla": bool(reporte),
                    "datos_reporte": (
                        {
                            "foto_url": (
                                request.build_absolute_uri(reporte.foto_trabajo.url)
                                if reporte and reporte.foto_trabajo
                                else None
                            ),
                            "comentario": reporte.comentario if reporte else None,
                            "fecha": fecha_resolucion.isoformat() if fecha_resolucion else None,
                            "jefe_cuadrilla": (
                                reporte.jefe_cuadrilla.username
                                if reporte and reporte.jefe_cuadrilla
                                else None
                            ),
                        }
                        if reporte
                        else None
                    ),
                }
            )

        return JsonResponse(dataset, safe=False)

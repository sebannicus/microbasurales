"""Servicios dedicados a la exportación de datos del módulo Analítica."""

from __future__ import annotations

import csv
from datetime import date, datetime, time
from typing import Tuple

from django.http import HttpResponse
from django.utils import timezone

from denuncias.models import Denuncia


def _rango_mes(fecha: date) -> Tuple[datetime, datetime]:
    """Retorna las fechas de inicio y término (exclusivo) del mes indicado."""

    fecha_base = fecha.replace(day=1)
    if fecha.month == 12:
        siguiente_mes = date(fecha.year + 1, 1, 1)
    else:
        siguiente_mes = date(fecha.year, fecha.month + 1, 1)

    tz = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(fecha_base, time.min), tz)
    fin = timezone.make_aware(datetime.combine(siguiente_mes, time.min), tz)
    return inicio, fin


def calcular_tiempo_resolucion_horas(denuncia: Denuncia) -> float | None:
    """Calcula el tiempo de resolución (en horas) para una denuncia."""

    reporte = getattr(denuncia, "reporte_cuadrilla", None)
    if not reporte or not reporte.fecha_reporte:
        return None

    delta = reporte.fecha_reporte - denuncia.fecha_creacion
    return round(delta.total_seconds() / 3600, 2)


def generar_csv_mensual(fecha_referencia: date | None = None) -> HttpResponse:
    """Genera el CSV correspondiente al mes solicitado (o mes actual)."""

    fecha_objetivo = fecha_referencia or timezone.localdate()
    inicio, fin = _rango_mes(fecha_objetivo)

    queryset = (
        Denuncia.objects.filter(fecha_creacion__gte=inicio, fecha_creacion__lt=fin)
        .select_related("reporte_cuadrilla", "reporte_cuadrilla__jefe_cuadrilla")
        .order_by("-fecha_creacion")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f"attachment; filename=informes_microbasurales_{fecha_objetivo.strftime('%m-%Y')}.csv"
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "id",
            "fecha_creacion",
            "estado",
            "zona",
            "tiempo_respuesta_horas",
            "funcionario_a_cargo",
            "fecha_resolucion",
            "tiene_reporte_cuadrilla",
        ]
    )

    for denuncia in queryset:
        reporte = getattr(denuncia, "reporte_cuadrilla", None)
        fecha_resolucion = None
        if reporte and reporte.fecha_reporte:
            fecha_resolucion = timezone.localtime(reporte.fecha_reporte)

        writer.writerow(
            [
                denuncia.id,
                timezone.localtime(denuncia.fecha_creacion).strftime("%Y-%m-%d %H:%M"),
                denuncia.estado,
                denuncia.zona or "Sin zona",
                calcular_tiempo_resolucion_horas(denuncia) or "",
                denuncia.cuadrilla_asignada or "No asignada",
                fecha_resolucion.strftime("%Y-%m-%d %H:%M") if fecha_resolucion else "",
                "SI" if reporte else "NO",
            ]
        )

    return response

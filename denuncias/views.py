import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import OperationalError, ProgrammingError, connection
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import ReporteCuadrillaForm
from .models import Denuncia, DenunciaNotificacion, EstadoDenuncia
from .permissions import IsFuncionarioMunicipal, PuedeEditarDenunciasFinalizadas
from .serializers import (
    DenunciaAdminSerializer,
    DenunciaCiudadanoSerializer,
    DenunciaSerializer,
    NotificacionDenunciaSerializer,
)
from .utils import obtener_zona_por_coordenadas


logger = logging.getLogger(__name__)


def _build_estado_q(estado):
    equivalentes = EstadoDenuncia.equivalent_values(estado)
    if not equivalentes:
        return None

    condicion = Q()
    for valor in equivalentes:
        condicion |= Q(estado__iexact=valor)
    return condicion


def _aplicar_filtro_estado(queryset, estado, *, excluir=False):
    condicion = _build_estado_q(estado)
    if not condicion:
        return queryset

    if excluir:
        return queryset.exclude(condicion)
    return queryset.filter(condicion)


class DenunciasPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class DenunciaListCreateView(APIView):
    """Permite listar todas las denuncias y crear nuevas denuncias."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = (
            Denuncia.objects.select_related(
                "usuario",
                "reporte_cuadrilla",
                "reporte_cuadrilla__jefe_cuadrilla",
            )
            .all()
        )

        estado = request.query_params.get("estado")
        if estado:
            queryset = _aplicar_filtro_estado(queryset, estado)

        serializer = DenunciaSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        descripcion = request.data.get("descripcion", "").strip()
        direccion_textual = request.data.get("direccion_textual", "").strip()
        latitud = request.data.get("latitud")
        longitud = request.data.get("longitud")
        direccion = request.data.get("direccion", "").strip()
        imagen = request.FILES.get("imagen")

        if not descripcion:
            return Response(
                {"descripcion": ["Este campo es requerido."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not direccion_textual:
            return Response(
                {"direccion_textual": ["Este campo es requerido."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            latitud_valor = float(latitud)
            longitud_valor = float(longitud)
        except (TypeError, ValueError):
            return Response(
                {"ubicacion": ["Debes proporcionar una ubicación válida."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if imagen is None:
            return Response(
                {"imagen": ["Debes adjuntar una fotografía del microbasural."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        zona_calculada = obtener_zona_por_coordenadas(
            latitud_valor,
            longitud_valor,
        )

        denuncia = Denuncia.objects.create(
            usuario=request.user,
            descripcion=descripcion,
            direccion_textual=direccion_textual,
            imagen=imagen,
            latitud=latitud_valor,
            longitud=longitud_valor,
            direccion=direccion,
            zona=zona_calculada,
        )

        serializer = DenunciaSerializer(denuncia, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MisDenunciasListView(generics.ListAPIView):
    """Lista únicamente las denuncias del usuario autenticado."""

    serializer_class = DenunciaCiudadanoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Denuncia.objects.filter(usuario=self.request.user)
            .select_related("reporte_cuadrilla", "reporte_cuadrilla__jefe_cuadrilla")
            .order_by("-fecha_creacion")
        )


class MiDenunciaRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """Permite obtener y actualizar una denuncia propia."""

    serializer_class = DenunciaCiudadanoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Denuncia.objects.filter(usuario=self.request.user)
            .select_related("reporte_cuadrilla", "reporte_cuadrilla__jefe_cuadrilla")
        )

    def perform_update(self, serializer):
        serializer.save(usuario=self.request.user)


class DenunciaAdminListView(generics.ListAPIView):
    """Lista de denuncias con filtros para funcionarios municipales."""

    serializer_class = DenunciaAdminSerializer
    permission_classes = [permissions.IsAuthenticated, IsFuncionarioMunicipal]
    pagination_class = DenunciasPagination

    def get_queryset(self):
        queryset = Denuncia.objects.select_related(
            "usuario",
            "reporte_cuadrilla",
            "reporte_cuadrilla__jefe_cuadrilla",
        ).all()

        estado = self.request.query_params.get("estado")
        if estado:
            queryset = _aplicar_filtro_estado(queryset, estado)

        excluir_estado = self.request.query_params.get("excluir_estado")
        if excluir_estado:
            queryset = _aplicar_filtro_estado(
                queryset, excluir_estado, excluir=True
            )

        solo_activos = self.request.query_params.get("solo_activos")
        if solo_activos is not None:
            valor_normalizado = str(solo_activos).lower()
            if valor_normalizado in {"1", "true", "t", "yes", "on"}:
                queryset = _aplicar_filtro_estado(
                    queryset, Denuncia.EstadoDenuncia.FINALIZADO, excluir=True
                )

        zona = self.request.query_params.get("zona")
        if zona:
            queryset = queryset.filter(zona__iexact=zona)

        fecha_desde = parse_date(self.request.query_params.get("fecha_desde", ""))
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)

        fecha_hasta = parse_date(self.request.query_params.get("fecha_hasta", ""))
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)

        return queryset.order_by("fecha_creacion")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class DenunciaAdminUpdateView(generics.UpdateAPIView):
    """Permite actualizar estado y cuadrilla de una denuncia."""

    serializer_class = DenunciaAdminSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsFuncionarioMunicipal,
        PuedeEditarDenunciasFinalizadas,
    ]
    queryset = Denuncia.objects.select_related(
        "usuario",
        "reporte_cuadrilla",
        "reporte_cuadrilla__jefe_cuadrilla",
    ).all()
    http_method_names = ["patch", "put"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


def _tabla_notificaciones_disponible():
    """Verifica si la tabla de notificaciones existe en la base de datos."""

    try:
        tablas = connection.introspection.table_names()
    except (ProgrammingError, OperationalError):
        return False
    return DenunciaNotificacion._meta.db_table in tablas


class MisNotificacionesListView(generics.ListAPIView):
    """Devuelve las notificaciones de cambio de estado del usuario autenticado."""

    serializer_class = NotificacionDenunciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        if not _tabla_notificaciones_disponible():
            logger.warning(
                "No se pudieron cargar las notificaciones; ¿ejecutaste las migraciones?",
                exc_info=True,
            )
            return Response([], status=status.HTTP_200_OK)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = DenunciaNotificacion.objects.filter(usuario=self.request.user)
        solo_no_leidas = self.request.query_params.get("solo_no_leidas")
        if solo_no_leidas is not None:
            valor = str(solo_no_leidas).lower()
            if valor in {"1", "true", "t", "yes", "on"}:
                queryset = queryset.filter(leida=False)
        return queryset.order_by("-fecha_creacion")


class NotificacionActualizarView(generics.UpdateAPIView):
    """Permite marcar como leídas las notificaciones propias."""

    serializer_class = NotificacionDenunciaSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["patch"]

    def get_queryset(self):
        if not _tabla_notificaciones_disponible():
            logger.warning(
                "No se pudieron actualizar las notificaciones; ¿ejecutaste las migraciones?",
                exc_info=True,
            )
            return DenunciaNotificacion.objects.none()

        return DenunciaNotificacion.objects.filter(usuario=self.request.user)


def _usuario_puede_gestionar_denuncias(usuario) -> bool:
    """Devuelve ``True`` si el usuario tiene permisos de fiscalizador o administrador."""

    puede_gestionar = getattr(usuario, "puede_gestionar_denuncias", None)

    if callable(puede_gestionar):
        puede_gestionar = puede_gestionar()

    if puede_gestionar is None:
        puede_gestionar = getattr(usuario, "es_funcionario_municipal", False)

    return bool(puede_gestionar)


def _construir_panel_context(request, *, solo_activos=False, solo_finalizados=False):
    """Genera el contexto para el panel de fiscalizadores con filtros personalizados."""

    refresh = RefreshToken.for_user(request.user)
    estados_config = EstadoDenuncia.as_config()
    estados_por_valor = {estado["value"]: estado for estado in estados_config}
    try:
        zonas_disponibles = (
            Denuncia.objects.exclude(zona="")
            .order_by("zona")
            .values_list("zona", flat=True)
            .distinct()
        )
    except (ProgrammingError, OperationalError):
        zonas_disponibles = []
        logger.warning(
            "No se pudo cargar la lista de zonas disponibles; ¿ejecutaste las migraciones?",
            exc_info=True,
        )

    base_api_url = request.build_absolute_uri(reverse("denuncias_admin_list"))
    query_params = {}

    if solo_finalizados:
        query_params["estado"] = Denuncia.EstadoDenuncia.FINALIZADO
    elif solo_activos:
        query_params["solo_activos"] = "1"

    api_url = base_api_url
    if query_params:
        api_url = f"{base_api_url}?{urlencode(query_params)}"

    return {
        "access_token": str(refresh.access_token),
        "api_url": api_url,
        "api_update_url": request.build_absolute_uri(
            reverse("denuncias_admin_update", args=[0])
        ),
        "zonas_disponibles": zonas_disponibles,
        "estados_config": estados_config,
        "estados_por_valor": estados_por_valor,
        "solo_activos": bool(solo_activos and not solo_finalizados),
        "solo_finalizados": bool(solo_finalizados),
    }


def _panel_fiscalizador_response(request, *, solo_activos=False, solo_finalizados=False):
    if not _usuario_puede_gestionar_denuncias(request.user):
        return redirect("home")

    context = _construir_panel_context(
        request,
        solo_activos=solo_activos,
        solo_finalizados=solo_finalizados,
    )
    return render(request, "denuncias/panel_funcionario.html", context)


@login_required
def panel_cuadrilla(request):
    """Panel exclusivo para jefes de cuadrilla."""

    if not getattr(request.user, "es_jefe_cuadrilla", False):
        messages.error(request, "No tienes permisos para acceder a este panel.")
        return redirect("home_ciudadano")

    denuncias_en_gestion = (
        Denuncia.objects.filter(
            estado=Denuncia.EstadoDenuncia.EN_GESTION,
            reporte_cuadrilla__isnull=True,
        )
        .select_related("reporte_cuadrilla")
        .order_by("-fecha_creacion")
    )

    form = None
    selected_denuncia = None

    def _obtener_denuncia(denuncia_id):
        if not denuncia_id:
            return None
        try:
            return denuncias_en_gestion.get(pk=int(denuncia_id))
        except (Denuncia.DoesNotExist, ValueError, TypeError):
            return None

    if request.method == "POST":
        form = ReporteCuadrillaForm(request.POST, request.FILES)
        selected_denuncia = _obtener_denuncia(form.data.get("denuncia_id"))

        if form.is_valid():
            denuncia = selected_denuncia
            if not denuncia:
                form.add_error(
                    None,
                    "La denuncia seleccionada no está disponible para la cuadrilla.",
                )
            elif denuncia.reporte_cuadrilla:
                form.add_error(
                    None,
                    "Esta denuncia ya cuenta con un reporte cargado.",
                )
            else:
                reporte = form.save(commit=False)
                reporte.jefe_cuadrilla = request.user
                reporte.denuncia = denuncia
                reporte.save()

                denuncia.estado = EstadoDenuncia.REALIZADO
                denuncia.save(update_fields=["estado"])
                messages.success(request, "El reporte se cargó correctamente.")
                return redirect("panel_cuadrilla")
    else:
        selected_denuncia = _obtener_denuncia(request.GET.get("denuncia"))
        if selected_denuncia:
            form = ReporteCuadrillaForm(
                initial={"denuncia_id": selected_denuncia.pk}
            )

    context = {
        "denuncias": denuncias_en_gestion,
        "selected_denuncia": selected_denuncia,
        "form": form,
    }
    return render(request, "denuncias/panel_cuadrilla.html", context)


@login_required
def panel_fiscalizador_activos(request):
    """Panel principal que muestra solo denuncias activas."""

    return _panel_fiscalizador_response(request, solo_activos=True)


@login_required
def panel_fiscalizador_finalizados(request):
    """Panel con las denuncias marcadas como finalizadas."""

    return _panel_fiscalizador_response(request, solo_finalizados=True)


@login_required
def panel_denuncias_alias(request):
    """Alias para mantener compatibilidad con enlaces existentes del panel."""

    return _panel_fiscalizador_response(request, solo_activos=True)
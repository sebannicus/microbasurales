import logging

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import OperationalError, ProgrammingError
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Denuncia
from .permissions import IsFuncionarioMunicipal
from .serializers import DenunciaAdminSerializer, DenunciaSerializer


logger = logging.getLogger(__name__)


class DenunciasPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class DenunciaListCreateView(APIView):
    """Permite listar todas las denuncias y crear nuevas denuncias."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = Denuncia.objects.select_related("usuario").all()
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
        zona = request.data.get("zona", "").strip()
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

        denuncia = Denuncia.objects.create(
            usuario=request.user,
            descripcion=descripcion,
            direccion_textual=direccion_textual,
            imagen=imagen,
            latitud=latitud_valor,
            longitud=longitud_valor,
            direccion=direccion,
            zona=zona,
        )

        serializer = DenunciaSerializer(denuncia, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MisDenunciasListView(generics.ListAPIView):
    """Lista únicamente las denuncias del usuario autenticado."""

    serializer_class = DenunciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Denuncia.objects.filter(usuario=self.request.user)
            .order_by("-fecha_creacion")
        )


class MiDenunciaRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """Permite obtener y actualizar una denuncia propia."""

    serializer_class = DenunciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Denuncia.objects.filter(usuario=self.request.user)

    def perform_update(self, serializer):
        serializer.save(usuario=self.request.user)


class DenunciaAdminListView(generics.ListAPIView):
    """Lista de denuncias con filtros para funcionarios municipales."""

    serializer_class = DenunciaAdminSerializer
    permission_classes = [permissions.IsAuthenticated, IsFuncionarioMunicipal]
    pagination_class = DenunciasPagination

    def get_queryset(self):
        queryset = Denuncia.objects.select_related("usuario").all()

        estado = self.request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(estado=estado)

        zona = self.request.query_params.get("zona")
        if zona:
            queryset = queryset.filter(zona__iexact=zona)

        fecha_desde = parse_date(self.request.query_params.get("fecha_desde", ""))
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)

        fecha_hasta = parse_date(self.request.query_params.get("fecha_hasta", ""))
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class DenunciaAdminUpdateView(generics.UpdateAPIView):
    """Permite actualizar estado y cuadrilla de una denuncia."""

    serializer_class = DenunciaAdminSerializer
    permission_classes = [permissions.IsAuthenticated, IsFuncionarioMunicipal]
    queryset = Denuncia.objects.select_related("usuario").all()
    http_method_names = ["patch", "put"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class PanelFuncionarioView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Panel con mapa interactivo exclusivo para fiscalizadores y administradores."""

    template_name = "denuncias/panel_funcionario.html"

    def test_func(self):
        usuario = self.request.user

        if not usuario.is_authenticated:
            return False

        puede_gestionar = getattr(usuario, "puede_gestionar_denuncias", None)

        if callable(puede_gestionar):
            puede_gestionar = puede_gestionar()

        if puede_gestionar is None:
            puede_gestionar = getattr(usuario, "es_funcionario_municipal", False)

        return bool(puede_gestionar)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        refresh = RefreshToken.for_user(self.request.user)
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

        context.update(
            {
                "access_token": str(refresh.access_token),
                "api_url": self.request.build_absolute_uri(
                    reverse("denuncias_admin_list")
                ),
                "api_update_url": self.request.build_absolute_uri(
                    reverse("denuncias_admin_update", args=[0])
                ),
                "zonas_disponibles": zonas_disponibles,
            }
        )
        return context

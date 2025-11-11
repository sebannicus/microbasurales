from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Denuncia
from .serializers import CrearDenunciaSerializer, DenunciaSerializer


class DenunciaListCreateView(generics.ListCreateAPIView):
    """Permite listar todas las denuncias y crear nuevas denuncias."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Denuncia.objects.all().order_by("-fecha_creacion")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CrearDenunciaSerializer
        return DenunciaSerializer

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        denuncia = serializer.save(usuario=request.user)
        response_serializer = DenunciaSerializer(
            denuncia, context={"request": request}
        )
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class MisDenunciasListView(generics.ListAPIView):
    """Lista únicamente las denuncias del usuario autenticado."""

    serializer_class = DenunciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Denuncia.objects.filter(usuario=self.request.user)
            .order_by("-fecha_creacion")
        )

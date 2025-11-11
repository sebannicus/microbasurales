from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Denuncia
from .serializers import DenunciaSerializer


class DenunciaListCreateView(APIView):
    """Permite listar todas las denuncias y crear nuevas denuncias."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = Denuncia.objects.all().order_by("-fecha_creacion")
        serializer = DenunciaSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        descripcion = request.data.get("descripcion", "").strip()
        direccion_textual = request.data.get("direccion_textual", "").strip()
        latitud = request.data.get("latitud")
        longitud = request.data.get("longitud")
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

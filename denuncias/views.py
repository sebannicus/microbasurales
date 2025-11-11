# ================================
#   IMPORTS API REST
# ================================
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Denuncia
from .serializers import (
    DenunciaSerializer,
    CrearDenunciaSerializer
)

# ================================
#   API REST DE DENUNCIAS
# ================================

# ✅ 1. Crear denuncia (usuario autenticado)
class CrearDenunciaView(generics.CreateAPIView):
    serializer_class = CrearDenunciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


# ✅ 2. Listar todas las denuncias (público o autenticado)
class ListarDenunciasView(generics.ListAPIView):
    queryset = Denuncia.objects.all().order_by('-fecha_creacion')
    serializer_class = DenunciaSerializer


# ✅ 3. Obtener / actualizar / eliminar denuncia por ID
class DenunciaDetalleView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Denuncia.objects.all()
    serializer_class = DenunciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    # ✅ Solo el usuario dueño puede editar
    def put(self, request, *args, **kwargs):
        denuncia = self.get_object()
        if denuncia.usuario != request.user:
            return Response(
                {"error": "No puedes editar esta denuncia."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().put(request, *args, **kwargs)


# ✅ 4. Cambiar estado (solo fiscalizadores o admin)
class CambiarEstadoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            denuncia = Denuncia.objects.get(pk=pk)
        except Denuncia.DoesNotExist:
            return Response(
                {"error": "Denuncia no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        # ✅ Verificar rol
        if not hasattr(request.user, "rol") or request.user.rol not in ['fiscalizador', 'administrador']:
            return Response(
                {"error": "No tienes permisos para cambiar estados."},
                status=status.HTTP_403_FORBIDDEN
            )

        nuevo_estado = request.data.get('estado')

        if nuevo_estado not in ['pendiente', 'en_proceso', 'resuelta']:
            return Response(
                {"error": "Estado inválido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        denuncia.estado = nuevo_estado
        denuncia.save()

        return Response({"mensaje": "Estado actualizado correctamente."})


# ================================
#   VISTAS HTML
# ================================
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")   # ✅ ESTA ES LA PARTE IMPORTANTE
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
            return redirect("login_django")  # O el nombre de tu URL

    return render(request, "login.html")


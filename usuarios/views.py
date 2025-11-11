from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import UsuarioRegistroSerializer

Usuario = get_user_model()


# ✅ REGISTRO API
class RegistroUsuarioView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioRegistroSerializer
    permission_classes = [AllowAny]


# ✅ LOGIN HTML (Formulario web)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            puede_gestionar = getattr(user, "puede_gestionar_denuncias", None)
            if callable(puede_gestionar):
                puede_gestionar = puede_gestionar()
            if puede_gestionar:
                return redirect("panel_denuncias")
            return redirect("home_ciudadano")
        messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "login.html", {"page": "login"})


# ✅ HOME HTML (vista protegida)
@login_required
def home_ciudadano_view(request):
    return render(request, "home_ciudadano.html")


def home_view(request):
    return render(request, "home.html")


# ✅ LOGOUT (HTML)
def logout_view(request):
    logout(request)
    return redirect("login_django")


# ✅ ENDPOINT PROTEGIDO /me/ (API REST con JWT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email or "No especificado",
        "rol": "Administrador" if user.is_staff else "Usuario",
        "mensaje": f"Autenticación válida. Bienvenido, {user.username}."
    })

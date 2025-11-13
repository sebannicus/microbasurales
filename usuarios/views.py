from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.utils.http import url_has_allowed_host_and_scheme
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from denuncias.models import Denuncia

from .forms import RegistroUsuarioForm
from .serializers import UsuarioRegistroSerializer

Usuario = get_user_model()


# ✅ REGISTRO API
class RegistroUsuarioView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioRegistroSerializer
    permission_classes = [AllowAny]


# ✅ LOGIN HTML (Formulario web)
def login_view(request):
    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            rol_usuario = getattr(user, "rol", None)
            roles_validos = {choice[0] for choice in Usuario.Roles.choices}

            if not rol_usuario or rol_usuario not in roles_validos:
                messages.error(
                    request,
                    "Tu cuenta no tiene un rol válido asignado. Contacta al administrador.",
                )
                return redirect("login_django")

            login(request, user)

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            if rol_usuario == Usuario.Roles.CIUDADANO:
                return redirect("home")

            if rol_usuario in {
                Usuario.Roles.FISCALIZADOR,
                Usuario.Roles.ADMINISTRADOR,
            } or getattr(user, "es_administrador", False):
                return redirect("panel_fiscalizador_activos")

            logout(request)
            messages.error(
                request,
                "Tu rol no tiene una redirección configurada en el sistema.",
            )
            return redirect("login_django")
        messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "login.html", {"page": "login"})


@require_http_methods(["GET", "POST"])
def register_view(request):
    form = RegistroUsuarioForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tu cuenta se creó correctamente. Ahora puedes iniciar sesión.")
        return redirect("login_django")

    return render(
        request,
        "usuarios/registro.html",
        {
            "form": form,
            "page": "register",
        },
    )


# ✅ HOME HTML (vista protegida)
@login_required
def home_ciudadano_view(request):
    """Vista principal que delega en ``home_view`` para las reglas de rol."""

    return home_view(request)


@login_required
def home_view(request):
    rol_usuario = getattr(request.user, "rol", None)

    if rol_usuario != Usuario.Roles.CIUDADANO:
        return redirect("panel_fiscalizador_activos")

    denuncias_usuario = (
        Denuncia.objects.filter(usuario=request.user)
        .select_related("usuario")
        .order_by("-fecha_creacion")
    )

    return render(
        request,
        "home_ciudadano.html",
        {"denuncias": denuncias_usuario},
    )


# ✅ LOGOUT (HTML)
@login_required
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

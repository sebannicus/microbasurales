from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_http_methods
from django.utils.http import url_has_allowed_host_and_scheme
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from denuncias.models import Denuncia
from denuncias.serializers import DenunciaCiudadanoSerializer

from .forms import PasswordChangeCustomForm, RegistroUsuarioForm, UserUpdateForm
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


@login_required
@require_http_methods(["GET", "POST"])
def crear_funcionario_view(request):
    if not getattr(request.user, "es_administrador", False):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect("home")

    roles_disponibles = [
        (Usuario.Roles.FISCALIZADOR, "Fiscalizador"),
        (Usuario.Roles.JEFE_CUADRILLA, "Jefe de cuadrilla"),
    ]

    rol_seleccionado = request.POST.get("rol") or roles_disponibles[0][0]
    form = RegistroUsuarioForm(request.POST or None)

    if request.method == "POST":
        if rol_seleccionado not in {opcion[0] for opcion in roles_disponibles}:
            messages.error(request, "Selecciona un rol válido para el nuevo funcionario.")
        elif form.is_valid():
            nuevo_usuario = form.save(rol=rol_seleccionado)
            messages.success(
                request,
                f"El usuario {nuevo_usuario.username} fue creado como {dict(roles_disponibles)[rol_seleccionado]}.",
            )
            return redirect("crear_funcionario")

    return render(
        request,
        "usuarios/crear_funcionarios.html",
        {
            "form": form,
            "roles_disponibles": roles_disponibles,
            "rol_seleccionado": rol_seleccionado,
        },
    )


def aviso_legal_view(request):
    return render(request, "aviso_legal.html")


def politica_privacidad_view(request):
    return render(request, "politica_privacidad.html")


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

    denuncias_serializadas = DenunciaCiudadanoSerializer(
        denuncias_usuario,
        many=True,
        context={"request": request},
    ).data

    return render(
        request,
        "home_ciudadano.html",
        {
            "denuncias": denuncias_usuario,
            "denuncias_json": denuncias_serializadas,
        },
    )


@login_required
def logout_view(request):
    """Cierra la sesión y redirige al formulario de login HTML."""

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
        "mensaje": f"Autenticación válida. Bienvenido, {user.username}.",
    })


class PerfilBaseView(LoginRequiredMixin, View):
    template_name = "usuarios/perfil.html"

    def build_context(self, request, **kwargs):
        return {
            "usuario": request.user,
            "user_form": kwargs.get("user_form")
            or UserUpdateForm(instance=request.user),
            "password_form": kwargs.get("password_form")
            or PasswordChangeCustomForm(user=request.user),
        }


class PerfilView(PerfilBaseView):
    def get(self, request):
        return render(request, self.template_name, self.build_context(request))

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("perfil")

        messages.error(request, "Por favor corrige los errores para continuar.")
        context = self.build_context(request, user_form=form)
        return render(request, self.template_name, context)


class PerfilPasswordUpdateView(PerfilBaseView):
    def get(self, request):
        return redirect("perfil")

    def post(self, request):
        form = PasswordChangeCustomForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data["new_password1"])
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Tu contraseña se actualizó correctamente.")
            return redirect("perfil")

        messages.error(request, "No se pudo actualizar la contraseña. Revisa los datos.")
        context = self.build_context(request, password_form=form)
        return render(request, self.template_name, context)

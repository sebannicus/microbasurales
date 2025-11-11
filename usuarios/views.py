from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .serializers import UsuarioRegistroSerializer

Usuario = get_user_model()


# ✅ REGISTRO API
class RegistroUsuarioView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioRegistroSerializer
    permission_classes = [AllowAny]


# ✅ LOGIN HTML (plantilla roja)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home_ciudadano")
        messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "login.html", {"page": "login"})


@login_required
def home_ciudadano_view(request):
    return render(request, "home_ciudadano.html")


from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegistroUsuarioView,
    aviso_legal_view,
    home_view,
    login_view,
    logout_view,
    me_view,
    PerfilPasswordUpdateView,
    PerfilView,
    politica_privacidad_view,
    register_view,
)


urlpatterns = [
    # LOGIN HTML (plantilla roja)
    path('login-django/', login_view, name='login_django'),
    path('registrarse/', register_view, name='register'),
    path('aviso-legal/', aviso_legal_view, name='aviso_legal'),
    path('politica-de-privacidad/', politica_privacidad_view, name='politica_privacidad'),

    # REGISTRO API
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),

    # LOGIN JWT
    path('login/', TokenObtainPairView.as_view(), name='login'),

    # REFRESH JWT
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),

    path('logout/', logout_view, name='logout'),

    path('perfil/', PerfilView.as_view(), name='perfil'),
    path('perfil/cambiar-clave/', PerfilPasswordUpdateView.as_view(), name='perfil_cambiar_clave'),


    path('home/', home_view, name="home"),

    # ✅ Endpoint protegido API REST (JWT)
    path('me/', me_view, name='me'),

]

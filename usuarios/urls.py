from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegistroUsuarioView,
    home_view,
    login_view,
    logout_view,
    me_view,
    register_view,
)


urlpatterns = [
    # LOGIN HTML (plantilla roja)
    path('login-django/', login_view, name='login_django'),
    path('registrarse/', register_view, name='register'),

    # REGISTRO API
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),

    # LOGIN JWT
    path('login/', TokenObtainPairView.as_view(), name='login'),

    # REFRESH JWT
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),

    path('logout/', logout_view, name='logout'),


    path('home/', home_view, name="home"),

    # ✅ Endpoint protegido API REST (JWT)
    path('me/', me_view, name='me'),

]

from django.contrib.auth.views import LogoutView
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from .views import RegistroUsuarioView, login_view

=======
from .views import RegistroUsuarioView, login_view, home_view, me_view
from django.contrib.auth.views import LogoutView


urlpatterns = [
    # LOGIN HTML (plantilla roja)
    path('login-django/', login_view, name='login_django'),

    # REGISTRO API
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),

    # LOGIN JWT
    path('login/', TokenObtainPairView.as_view(), name='login'),

    # REFRESH JWT
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),

    path('logout/', LogoutView.as_view(next_page='login_django'), name='logout'),

=======
    path('home/', home_view, name="home"),

    # ✅ Endpoint protegido API REST (JWT)
    path('me/', me_view, name='me'),

]

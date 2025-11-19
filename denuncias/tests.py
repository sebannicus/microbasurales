"""Tests para la app de denuncias."""

import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Denuncia, EstadoDenuncia, ReporteCuadrilla


class PanelCuadrillaViewTests(TestCase):
    """Cobertura básica sobre el flujo del panel de cuadrilla."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        usuario_model = get_user_model()
        cls.jefe = usuario_model.objects.create_user(
            username="jefe", password="pass1234", rol=usuario_model.Roles.JEFE_CUADRILLA
        )
        cls.ciudadano = usuario_model.objects.create_user(
            username="vecino", password="pass1234", rol=usuario_model.Roles.CIUDADANO
        )

    def crear_denuncia(self, **extra):
        valores = {
            "usuario": self.ciudadano,
            "descripcion": extra.get("descripcion", "Basural"),
            "direccion_textual": extra.get("direccion_textual", "Calle 123"),
            "latitud": extra.get("latitud", -33.45),
            "longitud": extra.get("longitud", -70.66),
            "estado": extra.get("estado", EstadoDenuncia.PENDIENTE),
        }
        valores.update(extra)
        return Denuncia.objects.create(**valores)

    def _crear_imagen(self):
        buffer = io.BytesIO()
        imagen = Image.new("RGB", (10, 10), color=(255, 0, 0))
        imagen.save(buffer, format="JPEG")
        buffer.seek(0)
        return SimpleUploadedFile("foto.jpg", buffer.read(), content_type="image/jpeg")

    def test_panel_requiere_rol_jefe(self):
        self.client.login(username="vecino", password="pass1234")
        response = self.client.get(reverse("panel_cuadrilla"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home_ciudadano"))

    def test_panel_lista_solo_en_gestion(self):
        denuncia_en_gestion = self.crear_denuncia(estado=EstadoDenuncia.EN_GESTION)
        self.crear_denuncia(estado=EstadoDenuncia.PENDIENTE)

        self.client.login(username="jefe", password="pass1234")
        response = self.client.get(reverse("panel_cuadrilla"))
        self.assertEqual(response.status_code, 200)
        denuncias_contexto = list(response.context["denuncias"])
        self.assertIn(denuncia_en_gestion, denuncias_contexto)
        self.assertTrue(all(d.estado == EstadoDenuncia.EN_GESTION for d in denuncias_contexto))

    def test_envio_reporte_crea_registro(self):
        denuncia = self.crear_denuncia(estado=EstadoDenuncia.EN_GESTION)
        self.client.login(username="jefe", password="pass1234")

        imagen = self._crear_imagen()
        response = self.client.post(
            reverse("panel_cuadrilla"),
            {
                "denuncia_id": denuncia.id,
                "comentario": "Trabajo realizado",
                "foto_trabajo": imagen,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("panel_cuadrilla"))

        denuncia.refresh_from_db()
        self.assertIsNotNone(denuncia.reporte_cuadrilla)
        self.assertEqual(denuncia.estado, EstadoDenuncia.REALIZADO)
        reporte = ReporteCuadrilla.objects.get(denuncia=denuncia)
        self.assertEqual(reporte.jefe_cuadrilla, self.jefe)
        self.assertEqual(reporte.comentario, "Trabajo realizado")

# Despliegue rápido en PythonAnywhere

La configuración del proyecto ahora se puede controlar con variables de entorno, por lo que no es necesario modificar el código fuente para apuntar al entorno de producción. A continuación se describe un flujo sugerido para publicar temporalmente el sitio en `christiangalindez.pythonanywhere.com`.

## 1. Preparar el código en PythonAnywhere
1. Inicia sesión en PythonAnywhere y abre una consola **Bash**.
2. Clona el repositorio en tu carpeta de usuario:
   ```bash
   cd ~
   git clone https://<tu-repo>/microbasurales.git
   cd microbasurales
   ```
3. Crea un entorno virtual con Python 3.11 y activa el entorno:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## 2. Variables de entorno recomendadas
Edita el archivo WSGI de la app (Web ▸ tu app ▸ **WSGI configuration file**) y, antes de importar `get_wsgi_application`, exporta las variables necesarias:

```python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "<clave-segura>")
os.environ.setdefault("DJANGO_DEBUG", "False")
os.environ.setdefault(
    "DJANGO_ALLOWED_HOSTS", "christiangalindez.pythonanywhere.com"
)
# Base de datos MySQL de PythonAnywhere
os.environ.setdefault("DB_ENGINE", "mysql")
os.environ.setdefault("DB_NAME", "christiangalindez$microbasurales")
os.environ.setdefault("DB_USER", "christiangalindez")
os.environ.setdefault("DB_PASSWORD", "<tu-password>")
os.environ.setdefault(
    "DB_HOST", "christiangalindez.mysql.pythonanywhere-services.com"
)
os.environ.setdefault("DB_PORT", "3306")
```

> 💡 Para una demo rápida sin MySQL puedes usar SQLite estableciendo `DB_ENGINE=sqlite`. El archivo `db.sqlite3` se creará dentro del proyecto.

## 3. Migraciones y usuario admin
Desde la consola Bash del proyecto (con el entorno virtual activado) ejecuta:
```bash
python manage.py migrate
python manage.py createsuperuser
```

## 4. Archivos estáticos y media
1. Corre `python manage.py collectstatic --noinput` para poblar `staticfiles/`.
2. En la pestaña Web ▸ **Static files** agrega:
   - URL: `/static/` → Directorio: `/home/christiangalindez/microbasurales/staticfiles`
   - URL: `/media/` → Directorio: `/home/christiangalindez/microbasurales/media`

## 5. Reinicia la app web
Pulsa **Reload** desde la pestaña Web para aplicar los cambios. Con esto la aplicación debería estar disponible en `https://christiangalindez.pythonanywhere.com/`.

## 6. Checklist rápido
- [ ] Variables de entorno configuradas.
- [ ] Migraciones ejecutadas.
- [ ] Usuario admin creado.
- [ ] Static/Media configurados.
- [ ] App reiniciada.

Siguiendo estos pasos tendrás el proyecto listo para ser mostrado temporalmente al profesor.

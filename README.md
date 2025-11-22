Manual de instalación local (desarrollo)
###################################################################################

1) Requisitos previos
- Git y Python 3.11+ instalados.
- PostgreSQL en tu máquina local.
- Credenciales por defecto para la base de datos (según config/settings.py):
USER: postgres
PASSWORD: 30102897
HOST: 127.0.0.1
PORT: 5432
- Dependencias Python listadas en requirements.txt.
###################################################################################
2) Clonar el repositorio
git clone microbasurales
cd microbasurales
###################################################################################
3) Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate (Windows: .venv\Scripts\activate)
###################################################################################
5) Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
###################################################################################
6) Configurar la base de datos PostgreSQL
Inicia el servicio PostgreSQL.
Crea la base de datos:
createdb microbasurales
Asegúrate que las credenciales coincidan con config/settings.py.
###################################################################################
7) Migraciones y superusuario
python manage.py migrate
python manage.py createsuperuser
###################################################################################
8) Archivos estáticos y media
Static: desde /static/
Media: se guarda en /media/
###################################################################################
9) Ejecutar servidor local
python manage.py runserver
Acceso: http://127.0.0.1:8000/
###################################################################################
10) Notas adicionales
- Autenticación JWT + sesiones.
- Idioma: es-CL.
- Zona horaria: America/Santiago.

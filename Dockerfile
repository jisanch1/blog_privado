# my_private_blog/Dockerfile

# Usar una imagen base de Python oficial (versión slim para reducir tamaño)
FROM python:3.10-slim-buster

# Establecer variables de entorno para Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias
# (por ejemplo, para psycopg2-binary que se conecta a PostgreSQL)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requisitos e instalar las dependencias de Python
# Primero copia solo requirements.txt para aprovechar el cache de Docker
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . /app/

# Recolectar archivos estáticos para producción
# STATIC_ROOT es donde Django los recolecta
RUN python manage.py collectstatic --noinput

# Comando para ejecutar la aplicación con Gunicorn
# Gunicorn es un servidor WSGI para aplicaciones Python en producción
# --bind 0.0.0.0:${PORT} es crucial para Cloud Run, que asigna un puerto dinámicamente
# private_blog_project.wsgi:application apunta al archivo WSGI de tu proyecto Django
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "private_blog_project.wsgi:application"]

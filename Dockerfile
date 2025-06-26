# my_private_blog/Dockerfile

# Usar una imagen base de Python oficial (versión slim para reducir tamaño)
FROM python:3.10-slim-buster

# Establecer variables de entorno para Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        wget \  # Añadir wget para descargar el proxy
    && rm -rf /var/lib/apt/lists/*

# Descargar e instalar el Cloud SQL Proxy
# Asegúrate de usar la arquitectura correcta (amd64 para la mayoría de los despliegues de Cloud Run)
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /usr/local/bin/cloud_sql_proxy \
    && chmod +x /usr/local/bin/cloud_sql_proxy

# Copiar el archivo de requisitos e instalar las dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . /app/

# Recolectar archivos estáticos para producción
RUN python manage.py collectstatic --noinput

# Configurar el puerto que Cloud Run asignará
ENV PORT 8080

# Comando para ejecutar la aplicación con Gunicorn
# Ejecutamos el proxy en segundo plano, esperamos un momento, y luego iniciamos Gunicorn.
# Usamos un script de entrada para manejar esto.
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# CMD que ejecuta nuestro script de entrada
CMD ["/app/entrypoint.sh"]

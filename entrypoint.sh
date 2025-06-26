# my_private_blog/entrypoint.sh

#!/bin/bash
set -e

# Variable de entorno de Cloud Run que tendrá el nombre de conexión
# del Cloud SQL Proxy.
# Necesitas configurar CLOUD_SQL_CONNECTION_NAME en las variables de entorno de tu servicio Cloud Run.
# Si CLOUD_SQL_CONNECTION_NAME NO está seteada, esto usará una cadena vacía,
# lo que causaría que el proxy falle si DATABASE_URL no está configurada para localhost
# o si no estás en un ambiente de Cloud Run.
CLOUD_SQL_CONNECTION_NAME="${CLOUD_SQL_CONNECTION_NAME}"

# Solo inicia el proxy si la variable CLOUD_SQL_CONNECTION_NAME está presente
# y si no estamos en DEBUG (o si la DATABASE_URL no es SQLite).
# Aquí estamos asumiendo que si CLOUD_SQL_CONNECTION_NAME existe, queremos usar Cloud SQL.
if [ -n "$CLOUD_SQL_CONNECTION_NAME" ]; then
    echo "Iniciando Cloud SQL Proxy para $CLOUD_SQL_CONNECTION_NAME..."
    # El proxy escucha en 127.0.0.1:5432 por defecto
    /usr/local/bin/cloud_sql_proxy -instances="${CLOUD_SQL_CONNECTION_NAME}"=tcp:5432 &
    # Pequeña pausa para dar tiempo al proxy a iniciar
    sleep 3
    echo "Cloud SQL Proxy iniciado."
fi

# Ejecutar Gunicorn
# Asegúrate de que Gunicorn escuche en el puerto definido por la variable de entorno PORT de Cloud Run
echo "Iniciando Gunicorn en puerto $PORT..."
exec gunicorn --bind "0.0.0.0:${PORT}" private_blog_project.wsgi:application

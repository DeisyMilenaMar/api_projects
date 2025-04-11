# api_projects
A Django-based project for developing and integrating web applications and APIs, streamlining data management, process automation, and seamless system interaction.

# Log Location and Access
Logs are saved at BASE_DIR/logs/api.log, with rotated files named api.log.1, api.log.2, etc.

View logs in real-time via: docker-compose logs -f web

# api_projects
A Django-based project for developing and integrating web applications and APIs, streamlining data management, process automation, and seamless system interaction.

# Log Location and Access
Logs are saved at BASE_DIR/logs/api.log, with rotated files named api.log.1, api.log.2, etc.

# Useful Docker Commands

# Cargar variables de entorno desde el archivo .env y desplegar la stack de Docker

export $(cat .env | xargs)
docker stack deploy -c docker-compose.yml binance_stack


# Ver logs del servicio de base de datos dentro de la stack

docker service logs binance_stack_db


# Ver logs del servicio "db" si estás usando docker-compose (sin stack)

docker-compose logs db


# Limpiar la terminal (opcional durante pruebas o depuración)

clear


# Listar los contenedores en ejecución

docker ps



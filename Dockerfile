# Etapa 1: Construcción
FROM python:3.10-buster AS builder

# Carga las variables de entorno desde el archivo .env
ENV APP_DIR=/API_PROJECTS

# Establece el directorio de trabajo
RUN mkdir -p ${APP_DIR}
WORKDIR ${APP_DIR}

# Instala las dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libssl-dev \
    libffi-dev \
    build-essential \
    python3-dev \
    libpq-dev \
    libcurl4-openssl-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copia solo los archivos necesarios para la instalación
COPY requirements.txt .

# Crea y activa un entorno virtual, actualiza pip e instala dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Etapa 2: Imagen final
FROM python:3.10-slim-buster

# Definir el directorio de trabajo
ENV APP_DIR=/API_PROJECTS
WORKDIR ${APP_DIR}

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar el entorno virtual de la etapa de construcción
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copia el código fuente del proyecto y el script entrypoint
COPY . .

RUN chmod +x ./scripts/start ./scripts/entrypoint.sh

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}

# Crea un usuario no-root para ejecutar la aplicación
RUN useradd -m appuser
USER appuser

# Expone el puerto en el que correrá la aplicación Django
EXPOSE 8000

# Cambia el ENTRYPOINT para usar 'sh' explícitamente
ENTRYPOINT ["sh", "./scripts/entrypoint.sh"]

# Cambia el CMD para usar 'sh' explícitamente
CMD ["sh", "./scripts/start"]
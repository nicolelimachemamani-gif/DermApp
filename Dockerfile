# Usar una imagen oficial de Python ligera
FROM python:3.10-slim

# Evitar que Python escriba archivos de caché .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Evitar que Python almacene en búfer las salidas de consola (útil para ver logs en tiempo real)
ENV PYTHONUNBUFFERED 1

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema mínimas necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias primero para aprovechar la caché de capas de Docker
COPY requirements.txt .

# Instalar dependencias de Python sin guardar caché para reducir tamaño del contenedor
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación al contenedor
COPY . .

# Exponer el puerto 5000 donde corre la app
EXPOSE 5000

# Comando por defecto para iniciar la aplicación en producción con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

# Usar una imagen base con Python y Playwright preinstalados
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar solo los archivos necesarios
COPY requirements.txt .
COPY *.py .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p archivos certificado logs

# Establecer variables de entorno por defecto
ENV PYTHONUNBUFFERED=1

# Comando por defecto (puede ser sobrescrito en docker-compose.yml)
CMD ["python", "Scrap_bci.py"] 
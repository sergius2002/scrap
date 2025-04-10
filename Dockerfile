# Usar una imagen base de Python
FROM python:3.10-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requisitos primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Instalar las dependencias de Playwright
RUN playwright install chromium
RUN playwright install-deps

# Copiar el resto de los archivos
COPY . .

# Crear directorios necesarios
RUN mkdir -p certificado archivos

# Variables de entorno
ENV PYTHONUNBUFFERED=1

# Comando por defecto (puede ser sobrescrito al ejecutar el contenedor)
CMD ["python", "facturador_lioren.py"] 